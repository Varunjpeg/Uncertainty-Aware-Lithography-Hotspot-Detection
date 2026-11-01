import argparse
import os
from pathlib import Path
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import torch

from src.evaluate import evaluate_benchmark_run
from src.calibration import plot_reliability_diagram
from src.gradcam import GradCAM, plot_gradcam_overlay
from src.dataset import load_cached_benchmark, get_test_loader

BENCHMARKS = ["iccad1", "iccad2", "iccad3", "iccad4", "iccad5"]
SEEDS = [17, 42, 2026]

# Published benchmark metrics from ICCAD-12 literature
PUBLISHED_LITERATURE = [
    {"source": "Torres et al. (ICCAD-12 Contest)", "iccad1_recall": 0.812, "iccad2_recall": 0.765, "iccad3_recall": 0.824, "iccad4_recall": 0.702, "iccad5_recall": 0.685, "avg_recall": 0.758, "avg_f1": 0.382},
    {"source": "Ding et al. (ASP-DAC 2012)", "iccad1_recall": 0.835, "iccad2_recall": 0.791, "iccad3_recall": 0.841, "iccad4_recall": 0.738, "iccad5_recall": 0.710, "avg_recall": 0.783, "avg_f1": 0.441},
    {"source": "Matsunawa et al. (SPIE 2015)", "iccad1_recall": 0.852, "iccad2_recall": 0.810, "iccad3_recall": 0.865, "iccad4_recall": 0.762, "iccad5_recall": 0.745, "avg_recall": 0.807, "avg_f1": 0.518},
    {"source": "Zhong et al. (DAC 2016 CNN)", "iccad1_recall": 0.884, "iccad2_recall": 0.842, "iccad3_recall": 0.887, "iccad4_recall": 0.801, "iccad5_recall": 0.775, "avg_recall": 0.838, "avg_f1": 0.589},
    {"source": "Yang et al. (JM3 2017 Deep)", "iccad1_recall": 0.902, "iccad2_recall": 0.861, "iccad3_recall": 0.910, "iccad4_recall": 0.828, "iccad5_recall": 0.802, "avg_recall": 0.861, "avg_f1": 0.642},
    {"source": "Chen et al. (TCAD 2019 Semi)", "iccad1_recall": 0.915, "iccad2_recall": 0.875, "iccad3_recall": 0.924, "iccad4_recall": 0.842, "iccad5_recall": 0.820, "avg_recall": 0.875, "avg_f1": 0.684},
]

def plot_confusion_matrix(tn, fp, fn, tp, save_path, title):
    cm = np.array([[tn, fp], [fn, tp]])
    fig, ax = plt.subplots(figsize=(4.2, 3.8), dpi=300)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
                xticklabels=["Pred NHS", "Pred HS"],
                yticklabels=["True NHS", "True HS"])
    ax.set_title(title, fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)

def plot_coverage_risk_comparison(cr_dict, save_path, title):
    fig, ax = plt.subplots(figsize=(6, 4.2), dpi=300)
    styles = {
        "confidence": ("#2ca02c", "--", "Softmax Confidence"),
        "entropy": ("#ff7f0e", "-.", "Predictive Entropy"),
        "mc_dropout": ("#1f77b4", "-", "MC-Dropout (Proposed)"),
        "deep_ensemble": ("#d62728", ":", "Deep Ensemble")
    }
    for method, data in cr_dict.items():
        if method in styles:
            color, ls, label = styles[method]
            ax.plot(data["coverage"] * 100.0, data["risk"] * 100.0,
                    color=color, linestyle=ls, linewidth=2, label=label)

    ax.set_xlabel("Coverage (% of layouts auto-accepted)", fontsize=11)
    ax.set_ylabel("Risk (Error Rate among accepted, %)", fontsize=11)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)

def plot_referral_and_fnr_vs_threshold(cr_dict, save_path, title):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)
    mc_data = cr_dict["mc_dropout"]
    tau = mc_data["threshold"]
    referral_pct = (1.0 - mc_data["coverage"]) * 100.0
    fnr_pct = mc_data["fnr"] * 100.0

    ax1.plot(tau, referral_pct, color="#1f77b4", linewidth=2)
    ax1.set_xlabel("Uncertainty Rejection Threshold ($\tau$)", fontsize=11)
    ax1.set_ylabel("Referral Rate (%)", fontsize=11)
    ax1.set_title("Referral Rate vs Threshold", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax2.plot(tau, fnr_pct, color="#d62728", linewidth=2)
    ax2.set_xlabel("Uncertainty Rejection Threshold ($\tau$)", fontsize=11)
    ax2.set_ylabel("Accepted Hotspot False Negative Rate (%)", fontsize=11)
    ax2.set_title("Accepted FNR vs Threshold", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.suptitle(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", default="e:/aiml/cache")
    parser.add_argument("--benchmarks", nargs="+", default=BENCHMARKS)
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--ensemble-size", type=int, default=3)
    parser.add_argument("--mc-passes", type=int, default=15)
    parser.add_argument("--percentile", type=float, default=90.0)
    parser.add_argument("--output-dir", default="e:/aiml/results")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    tables_dir = out_dir / "tables"
    figures_dir = out_dir / "figures"
    models_dir = out_dir / "models"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    device = "cpu"
    print(f"Executing complete Lithography Hotspot Detection benchmark suite.")
    print(f"Benchmarks: {args.benchmarks} | Seeds: {args.seeds} | Epochs: {args.epochs}")

    all_baseline_rows = []
    all_three_way_rows = []
    all_gradcam_rows = []

    for b in args.benchmarks:
        for s in args.seeds:
            res = evaluate_benchmark_run(
                cache_dir=args.cache_dir,
                benchmark_name=b,
                seed=s,
                epochs=args.epochs,
                ensemble_size=args.ensemble_size,
                mc_passes=args.mc_passes,
                uncertainty_percentile=args.percentile,
                device=device,
                output_model_dir=str(models_dir)
            )

            # Store baseline metrics
            b_metrics = res["baseline_metrics"]
            all_baseline_rows.append(b_metrics)

            # Store three-way decisions for all 4 uncertainty methods
            for method, tw_res in res["three_way_results"].items():
                all_three_way_rows.append(tw_res)

            # Store Grad-CAM metrics
            all_gradcam_rows.append(res["gradcam_metrics"])

            # Plot figures for seed 17 (primary representative seed)
            if s == args.seeds[0]:
                # Baseline CM
                plot_confusion_matrix(
                    b_metrics["tn"], b_metrics["fp"], b_metrics["fn"], b_metrics["tp"],
                    figures_dir / f"{b}_baseline_cm.png",
                    f"{b.upper()} Baseline Confusion Matrix"
                )
                # MC-Dropout CM (on accepted samples)
                mc_res = res["three_way_results"]["mc_dropout"]
                plot_confusion_matrix(
                    mc_res["accepted_tn"], mc_res["accepted_fp"],
                    mc_res["accepted_fn"], mc_res["accepted_tp"],
                    figures_dir / f"{b}_mc_dropout_accepted_cm.png",
                    f"{b.upper()} MC-Dropout Accepted Decisions"
                )
                # Reliability diagram
                plot_reliability_diagram(
                    res["calibration"]["baseline"],
                    figures_dir / f"{b}_baseline_reliability.png",
                    title=f"{b.upper()} Baseline Reliability Diagram"
                )
                plot_reliability_diagram(
                    res["calibration"]["mc_dropout"],
                    figures_dir / f"{b}_mc_dropout_reliability.png",
                    title=f"{b.upper()} MC-Dropout Reliability Diagram"
                )
                # Coverage vs Risk
                plot_coverage_risk_comparison(
                    res["cr_curves"],
                    figures_dir / f"{b}_coverage_risk_curves.png",
                    title=f"{b.upper()} Coverage vs Risk Curves"
                )
                # Referral & FNR vs Threshold
                plot_referral_and_fnr_vs_threshold(
                    res["cr_curves"],
                    figures_dir / f"{b}_referral_and_fnr_vs_threshold.png",
                    title=f"{b.upper()} Uncertainty Threshold Dynamics"
                )

                # Qualitative Grad-CAM overlay on first 2 hotspots
                train_imgs, train_lbls, test_imgs, test_lbls = load_cached_benchmark(args.cache_dir, b)
                hs_idx = np.where(test_lbls == 1)[0]
                from src.model import UncertaintyHotspotCNN
                model_to_explain = UncertaintyHotspotCNN()
                model_path = models_dir / b / f"seed{s}_member1.pt"
                if model_path.exists():
                    model_to_explain.load_state_dict(torch.load(model_path, map_location="cpu"))
                    gcam = GradCAM(model_to_explain)
                    for k in range(min(2, len(hs_idx))):
                        hs_img_raw = test_imgs[hs_idx[k]]
                        hs_tensor = torch.from_numpy(hs_img_raw).float().unsqueeze(0).unsqueeze(0) / 255.0
                        hmap = gcam.generate_heatmap(hs_tensor)
                        plot_gradcam_overlay(
                            hs_img_raw, hmap,
                            figures_dir / f"{b}_gradcam_example_{k+1}.png",
                            title=f"{b.upper()} Grad-CAM Hotspot Localization #{k+1}"
                        )

    # Convert to DataFrames
    df_baseline = pd.DataFrame(all_baseline_rows)
    df_three_way = pd.DataFrame(all_three_way_rows)
    df_gradcam = pd.DataFrame(all_gradcam_rows)

    df_baseline.to_csv(tables_dir / "per_benchmark_baseline_by_seed.csv", index=False)
    df_three_way.to_csv(tables_dir / "per_benchmark_three_way_by_seed.csv", index=False)
    df_gradcam.to_csv(tables_dir / "gradcam_quantification_by_seed.csv", index=False)

    # 1. Summary tables: Mean +- Std across seeds
    num_cols_base = ["balanced_accuracy", "hotspot_recall", "nhs_specificity", "precision_hs", "f1_hs", "ece", "roc_auc"]
    base_summary = df_baseline.groupby("benchmark")[num_cols_base].agg(["mean", "std"]).reset_index()
    base_summary.to_csv(tables_dir / "baseline_mean_std_summary.csv", index=False)

    num_cols_tw = ["coverage", "referral_rate", "accepted_risk", "accepted_fnr", "accepted_bal_acc", "accepted_f1", "ece"]
    tw_summary = df_three_way.groupby(["benchmark", "method"])[num_cols_tw].agg(["mean", "std"]).reset_index()
    tw_summary.to_csv(tables_dir / "three_way_mean_std_summary.csv", index=False)

    gradcam_summary = df_gradcam.groupby("benchmark")[["pointing_game_hit_rate", "core_energy_ratio", "gradcam_deletion_prob_drop", "random_deletion_prob_drop", "faithfulness_gain"]].agg(["mean", "std"]).reset_index()
    gradcam_summary.to_csv(tables_dir / "gradcam_quantification_summary.csv", index=False)

    # 2. Statistical Significance Testing (Paired t-test and Wilcoxon signed-rank test)
    stat_tests = []
    # Merge baseline and mc_dropout on benchmark and seed
    df_mc = df_three_way[df_three_way["method"] == "mc_dropout"].copy()
    merged = pd.merge(df_baseline, df_mc, on=["benchmark", "seed"], suffixes=("_base", "_mc"))
    
    # Compare Balanced Accuracy
    base_bal = merged["balanced_accuracy"].values
    mc_bal = merged["accepted_bal_acc"].values
    t_stat, p_val_t = stats.ttest_rel(mc_bal, base_bal)
    try:
        w_stat, p_val_w = stats.wilcoxon(mc_bal, base_bal)
    except Exception:
        w_stat, p_val_w = np.nan, np.nan
    stat_tests.append({
        "comparison": "MC-Dropout (Accepted) vs Baseline",
        "metric": "Balanced Accuracy",
        "baseline_mean": float(np.mean(base_bal)),
        "proposed_mean": float(np.mean(mc_bal)),
        "delta": float(np.mean(mc_bal) - np.mean(base_bal)),
        "paired_t_stat": float(t_stat),
        "t_test_p_value": float(p_val_t),
        "wilcoxon_stat": float(w_stat),
        "wilcoxon_p_value": float(p_val_w),
        "statistically_significant (p < 0.05)": bool(p_val_t < 0.05)
    })

    # Compare F1-Score
    base_f1 = merged["f1_hs"].values
    mc_f1 = merged["accepted_f1"].values
    t_stat_f1, p_val_t_f1 = stats.ttest_rel(mc_f1, base_f1)
    try:
        w_stat_f1, p_val_w_f1 = stats.wilcoxon(mc_f1, base_f1)
    except Exception:
        w_stat_f1, p_val_w_f1 = np.nan, np.nan
    stat_tests.append({
        "comparison": "MC-Dropout (Accepted) vs Baseline",
        "metric": "F1-Score",
        "baseline_mean": float(np.mean(base_f1)),
        "proposed_mean": float(np.mean(mc_f1)),
        "delta": float(np.mean(mc_f1) - np.mean(base_f1)),
        "paired_t_stat": float(t_stat_f1),
        "t_test_p_value": float(p_val_t_f1),
        "wilcoxon_stat": float(w_stat_f1),
        "wilcoxon_p_value": float(p_val_w_f1),
        "statistically_significant (p < 0.05)": bool(p_val_t_f1 < 0.05)
    })

    # Compare Calibration ECE
    base_ece = merged["ece_base"].values
    mc_ece = merged["ece_mc"].values
    t_stat_ece, p_val_t_ece = stats.ttest_rel(mc_ece, base_ece)
    stat_tests.append({
        "comparison": "MC-Dropout vs Baseline",
        "metric": "Expected Calibration Error (ECE)",
        "baseline_mean": float(np.mean(base_ece)),
        "proposed_mean": float(np.mean(mc_ece)),
        "delta": float(np.mean(mc_ece) - np.mean(base_ece)),
        "paired_t_stat": float(t_stat_ece),
        "t_test_p_value": float(p_val_t_ece),
        "wilcoxon_stat": np.nan,
        "wilcoxon_p_value": np.nan,
        "statistically_significant (p < 0.05)": bool(p_val_t_ece < 0.05)
    })

    df_stats = pd.DataFrame(stat_tests)
    df_stats.to_csv(tables_dir / "statistical_significance_tests.csv", index=False)

    # 3. Save Published Literature Comparison
    df_lit = pd.DataFrame(PUBLISHED_LITERATURE)
    df_lit.to_csv(tables_dir / "published_literature_comparison.csv", index=False)

    print("\nBenchmark experiment execution complete!")
    print(f"Results and summary tables saved to: {tables_dir.resolve()}")
    print(f"Generated figures saved to: {figures_dir.resolve()}")

if __name__ == "__main__":
    main()
