import os
import random
import numpy as np
import torch
from sklearn.metrics import (
    confusion_matrix, balanced_accuracy_score,
    recall_score, precision_score, f1_score, roc_auc_score
)
from src.dataset import (
    load_cached_benchmark,
    get_stratified_train_val_loaders,
    get_test_loader,
    HotspotCachedDataset
)
from src.model import UncertaintyHotspotCNN
from src.train import train_model, evaluate_loader
from src.uncertainty import (
    compute_uncertainty_scores,
    calibrate_threshold_on_validation,
    evaluate_three_way_decision,
    compute_coverage_risk_curve
)
from src.calibration import compute_calibration_metrics
from src.gradcam import quantify_gradcam_explanations

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

@torch.no_grad()
def collect_mc_dropout_probs(model, loader, device, passes=15):
    """
    Executes T stochastic forward passes with dropout active (and BatchNorm in eval).
    Loads batches ONCE from loader and executes T passes in memory.
    """
    model.enable_mc_dropout()
    pass_results = [[] for _ in range(passes)]

    for x_batch, _ in loader:
        x_batch = x_batch.to(device)
        for t in range(passes):
            logits = model(x_batch)
            probs = torch.sigmoid(logits).cpu().numpy()
            pass_results[t].append(probs)

    model.eval()
    all_passes = [np.concatenate(batch_list) for batch_list in pass_results]
    return np.stack(all_passes, axis=0)  # Shape: (passes, N)

def evaluate_benchmark_run(
    cache_dir,
    benchmark_name,
    seed=42,
    epochs=8,
    ensemble_size=3,
    mc_passes=15,
    uncertainty_percentile=90.0,
    device="cpu",
    output_model_dir=None
):
    """
    Executes a complete, controlled experimental evaluation for a single benchmark and seed.
    Strictly follows guidelines:
      - Stratified validation split for threshold tuning and checkpointing.
      - Test set evaluated once at the end.
      - Produces Baseline 2x2 confusion matrix and metrics.
      - Produces Three-Way decision metrics for all 4 uncertainty methods.
      - Quantifies Grad-CAM on hotspot samples.
    """
    set_seed(seed)
    print(f"\n=======================================================")
    print(f"Running Benchmark: {benchmark_name.upper()} | Seed: {seed} | Device: {device}")
    print(f"=======================================================")

    train_imgs, train_lbls, test_imgs, test_lbls = load_cached_benchmark(cache_dir, benchmark_name)
    b_size = 32 if len(train_lbls) < 1000 else 64
    train_loader, val_loader, pos_weight, n_train, n_val = get_stratified_train_val_loaders(
        train_imgs, train_lbls, seed=seed, val_fraction=0.20, batch_size=b_size
    )
    test_loader = get_test_loader(test_imgs, test_lbls, batch_size=256)

    pos_weight_adj = pos_weight * 1.5
    print(f"  Data splits: Train={n_train} (raw pos_weight={pos_weight:.2f}, adj={pos_weight_adj:.2f}) | Val={n_val} | Test={len(test_lbls)}")

    # Train ensemble members
    models = []
    for m in range(ensemble_size):
        print(f"  Training Model {m+1}/{ensemble_size}...")
        model = UncertaintyHotspotCNN()
        trained_model, best_val_bal_acc = train_model(
            model, train_loader, val_loader,
            pos_weight=pos_weight_adj, epochs=epochs, lr=2e-3, device=device, verbose=(m == 0)
        )
        models.append(trained_model)
        if output_model_dir:
            os.makedirs(f"{output_model_dir}/{benchmark_name}", exist_ok=True)
            torch.save(trained_model.state_dict(), f"{output_model_dir}/{benchmark_name}/seed{seed}_member{m+1}.pt")

    # Primary model (Member 1) for Baseline and MC-Dropout
    primary_model = models[0]

    # --- 1. Validation Set Probabilities & Threshold Tuning ---
    val_probs_members = []
    test_probs_members = []
    for model in models:
        vp, val_true = evaluate_loader(model, val_loader, device)
        tp, test_true = evaluate_loader(model, test_loader, device)
        val_probs_members.append(vp)
        test_probs_members.append(tp)

    val_probs_stack = np.stack(val_probs_members, axis=0)   # (M, N_val)
    test_probs_stack = np.stack(test_probs_members, axis=0) # (M, N_test)

    # Validation MC-Dropout
    val_mc_stack = collect_mc_dropout_probs(primary_model, val_loader, device, passes=mc_passes)
    test_mc_stack = collect_mc_dropout_probs(primary_model, test_loader, device, passes=mc_passes)

    # --- 2. Deterministic Baseline Evaluation on Official Test Set ---
    base_test_p = test_probs_members[0]
    base_pred = (base_test_p >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(test_true, base_pred, labels=[0, 1]).ravel()
    base_cal = compute_calibration_metrics(test_true, base_test_p)

    baseline_metrics = {
        "benchmark": benchmark_name,
        "seed": seed,
        "method": "deterministic_baseline",
        "n_test": len(test_true),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "balanced_accuracy": float(balanced_accuracy_score(test_true, base_pred)),
        "hotspot_recall": float(recall_score(test_true, base_pred, zero_division=0)),
        "nhs_specificity": float(tn / max(1, tn + fp)),
        "precision_hs": float(precision_score(test_true, base_pred, zero_division=0)),
        "f1_hs": float(f1_score(test_true, base_pred, zero_division=0)),
        "ece": base_cal["ece"],
        "mce": base_cal["mce"],
        "roc_auc": float(roc_auc_score(test_true, base_test_p)) if len(np.unique(test_true)) > 1 else np.nan,
    }

    # --- 3. Uncertainty Methods & Three-Way Decisions ---
    methods = ["confidence", "entropy", "mc_dropout", "deep_ensemble"]
    three_way_results = {}
    cr_curves = {}

    for method in methods:
        if method == "mc_dropout":
            v_p, v_u = compute_uncertainty_scores(method, val_mc_stack)
            t_p, t_u = compute_uncertainty_scores(method, test_mc_stack)
        elif method == "deep_ensemble":
            v_p, v_u = compute_uncertainty_scores(method, val_probs_stack)
            t_p, t_u = compute_uncertainty_scores(method, test_probs_stack)
        elif method == "confidence":
            v_p, v_u = compute_uncertainty_scores(method, val_probs_members[0])
            t_p, t_u = compute_uncertainty_scores(method, test_probs_members[0])
        elif method == "entropy":
            v_p, v_u = compute_uncertainty_scores(method, val_probs_members[0])
            t_p, t_u = compute_uncertainty_scores(method, test_probs_members[0])

        # Calibrate threshold strictly on validation uncertainty
        tau_val = calibrate_threshold_on_validation(v_u, percentile=uncertainty_percentile)

        # Apply threshold to unseen test set
        dec_res = evaluate_three_way_decision(test_true, t_p, t_u, tau_val)
        dec_res["benchmark"] = benchmark_name
        dec_res["seed"] = seed
        dec_res["method"] = method
        
        # Test calibration
        cal_res = compute_calibration_metrics(test_true, t_p)
        dec_res["ece"] = cal_res["ece"]

        # Calculate balanced accuracy and F1 on accepted samples
        is_acc = t_u <= tau_val
        if np.sum(is_acc) > 0 and len(np.unique(test_true[is_acc])) > 1:
            acc_pred = (t_p[is_acc] >= 0.5).astype(int)
            dec_res["accepted_bal_acc"] = float(balanced_accuracy_score(test_true[is_acc], acc_pred))
            dec_res["accepted_f1"] = float(f1_score(test_true[is_acc], acc_pred, zero_division=0))
            dec_res["accepted_precision"] = float(precision_score(test_true[is_acc], acc_pred, zero_division=0))
            dec_res["accepted_recall"] = float(recall_score(test_true[is_acc], acc_pred, zero_division=0))
        else:
            dec_res["accepted_bal_acc"] = np.nan
            dec_res["accepted_f1"] = np.nan
            dec_res["accepted_precision"] = np.nan
            dec_res["accepted_recall"] = np.nan

        three_way_results[method] = dec_res

        # Coverage-Risk curve points
        cr_curves[method] = compute_coverage_risk_curve(test_true, t_p, t_u)

    # --- 4. Quantified Grad-CAM Evaluation on Hotspots ---
    hs_indices = np.where(test_lbls == 1)[0]
    hs_eval_imgs = test_imgs[hs_indices]
    hs_eval_lbls = test_lbls[hs_indices]
    hs_eval_loader = get_test_loader(hs_eval_imgs, hs_eval_lbls, batch_size=1)
    
    gradcam_metrics = quantify_gradcam_explanations(
        primary_model, hs_eval_loader, device=device, core_box=(16, 48, 16, 48)
    )
    gradcam_metrics["benchmark"] = benchmark_name
    gradcam_metrics["seed"] = seed

    return {
        "benchmark": benchmark_name,
        "seed": seed,
        "baseline_metrics": baseline_metrics,
        "three_way_results": three_way_results,
        "cr_curves": cr_curves,
        "calibration": {
            "baseline": base_cal,
            "mc_dropout": compute_calibration_metrics(test_true, compute_uncertainty_scores("mc_dropout", test_mc_stack)[0])
        },
        "gradcam_metrics": gradcam_metrics,
        "test_labels": test_true,
        "test_probs_baseline": base_test_p,
        "test_probs_mc": compute_uncertainty_scores("mc_dropout", test_mc_stack)[0],
        "test_uncertainty_mc": compute_uncertainty_scores("mc_dropout", test_mc_stack)[1],
    }
