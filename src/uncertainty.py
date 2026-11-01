import numpy as np
import torch

def binary_entropy(p, eps=1e-7):
    """Computes binary Shannon entropy in bits, normalized to [0, 1]."""
    p = np.clip(p, eps, 1.0 - eps)
    return -(p * np.log2(p) + (1.0 - p) * np.log2(1.0 - p))

def compute_uncertainty_scores(method, p_samples):
    """
    Computes mean predictive probability and uncertainty score.
    p_samples: shape (T, N) for MC-Dropout / Ensemble, or (N,) for single-model.
    """
    p_samples = np.asarray(p_samples)
    if p_samples.ndim == 1:
        mean_p = p_samples
    else:
        mean_p = np.mean(p_samples, axis=0)

    if method == "confidence":
        # Margin uncertainty: distance from certainty (0.0 when confident, 0.5 when uncertain)
        uncertainty = 1.0 - np.maximum(mean_p, 1.0 - mean_p)
    elif method == "entropy":
        # Predictive entropy: 0 when confident, 1 when maximally uncertain (p=0.5)
        uncertainty = binary_entropy(mean_p)
    elif method == "mc_dropout":
        # Epistemic predictive variance across stochastic passes
        if p_samples.ndim > 1 and p_samples.shape[0] > 1:
            uncertainty = np.var(p_samples, axis=0, ddof=1)
        else:
            uncertainty = np.zeros_like(mean_p)
    elif method == "deep_ensemble":
        # Ensemble variance across independently trained models
        if p_samples.ndim > 1 and p_samples.shape[0] > 1:
            uncertainty = np.var(p_samples, axis=0, ddof=1)
        else:
            uncertainty = np.zeros_like(mean_p)
    else:
        raise ValueError(f"Unknown uncertainty method: {method}")

    return mean_p, uncertainty

def calibrate_threshold_on_validation(val_uncertainties, percentile=90.0):
    """
    Calibrates the rejection threshold tau strictly on the validation set.
    Samples with uncertainty > tau will be referred.
    """
    val_u = np.asarray(val_uncertainties)
    tau = float(np.percentile(val_u, percentile))
    return tau

def evaluate_three_way_decision(y_true, mean_p, uncertainty, tau):
    """
    Applies the three-way decision pipeline with threshold tau:
      - u > tau -> Referral
      - u <= tau and mean_p >= 0.5 -> Auto HS
      - u <= tau and mean_p < 0.5  -> Auto NHS
    """
    y_true = np.asarray(y_true).astype(int)
    mean_p = np.asarray(mean_p)
    uncertainty = np.asarray(uncertainty)

    is_referral = uncertainty > tau
    is_accepted = ~is_referral

    binary_pred = (mean_p >= 0.5).astype(int)

    n_total = len(y_true)
    n_referred = int(np.sum(is_referral))
    n_accepted = int(np.sum(is_accepted))

    coverage = float(n_accepted) / max(1, n_total)
    referral_rate = float(n_referred) / max(1, n_total)

    # Decisions breakdown
    auto_hs = int(np.sum((binary_pred == 1) & is_accepted))
    auto_nhs = int(np.sum((binary_pred == 0) & is_accepted))

    # Error analysis among accepted decisions
    if n_accepted > 0:
        accepted_errors = (binary_pred[is_accepted] != y_true[is_accepted]).astype(float)
        accepted_risk = float(np.mean(accepted_errors))
        
        # False Negatives (Hotspot predicted as NHS)
        accepted_hs_true = np.sum((y_true == 1) & is_accepted)
        accepted_fn = np.sum((y_true == 1) & (binary_pred == 0) & is_accepted)
        accepted_fnr = float(accepted_fn) / max(1, accepted_hs_true)

        # True Positives & False Positives among accepted
        accepted_tp = np.sum((y_true == 1) & (binary_pred == 1) & is_accepted)
        accepted_fp = np.sum((y_true == 0) & (binary_pred == 1) & is_accepted)
        accepted_tn = np.sum((y_true == 0) & (binary_pred == 0) & is_accepted)
    else:
        accepted_risk = 0.0
        accepted_fnr = 0.0
        accepted_tp = accepted_fp = accepted_tn = accepted_fn = 0

    # Hotspots saved by referral (referred true hotspots)
    referred_hs = int(np.sum((y_true == 1) & is_referral))
    referred_nhs = int(np.sum((y_true == 0) & is_referral))

    return {
        "tau": tau,
        "n_total": n_total,
        "n_accepted": n_accepted,
        "n_referred": n_referred,
        "coverage": coverage,
        "referral_rate": referral_rate,
        "accepted_risk": accepted_risk,
        "accepted_fnr": accepted_fnr,
        "auto_hs": auto_hs,
        "auto_nhs": auto_nhs,
        "accepted_tp": int(accepted_tp),
        "accepted_fp": int(accepted_fp),
        "accepted_tn": int(accepted_tn),
        "accepted_fn": int(accepted_fn),
        "referred_hs": referred_hs,
        "referred_nhs": referred_nhs,
    }

def compute_coverage_risk_curve(y_true, mean_p, uncertainty, num_points=100):
    """
    Computes the full Coverage vs Risk curve by sweeping uncertainty rejection thresholds.
    Sorts samples by increasing uncertainty: lowest uncertainty accepted first.
    """
    y_true = np.asarray(y_true).astype(int)
    mean_p = np.asarray(mean_p)
    uncertainty = np.asarray(uncertainty)

    sort_idx = np.argsort(uncertainty)
    y_sorted = y_true[sort_idx]
    p_sorted = mean_p[sort_idx]
    u_sorted = uncertainty[sort_idx]

    pred_sorted = (p_sorted >= 0.5).astype(int)
    errors = (pred_sorted != y_sorted).astype(float)
    is_fn = ((y_sorted == 1) & (pred_sorted == 0)).astype(float)

    coverages, risks, fnrs, thresholds = [], [], [], []
    n_total = len(y_true)

    # Sample points uniformly along coverage [0.01, 1.0]
    eval_counts = np.linspace(max(10, int(n_total * 0.05)), n_total, num_points, dtype=int)
    for k in eval_counts:
        cov = k / n_total
        risk = float(np.mean(errors[:k]))
        hs_count = np.sum(y_sorted[:k] == 1)
        fn_count = np.sum(is_fn[:k])
        fnr = float(fn_count) / max(1, hs_count)
        tau = float(u_sorted[k - 1])

        coverages.append(cov)
        risks.append(risk)
        fnrs.append(fnr)
        thresholds.append(tau)

    return {
        "coverage": np.array(coverages),
        "risk": np.array(risks),
        "fnr": np.array(fnrs),
        "threshold": np.array(thresholds),
    }
