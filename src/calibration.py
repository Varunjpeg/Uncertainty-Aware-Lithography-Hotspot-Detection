import numpy as np
import matplotlib.pyplot as plt

def compute_calibration_metrics(y_true, probs, n_bins=10):
    """
    Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).
    y_true: binary ground truth labels (0 or 1).
    probs: model predicted probabilities for class 1 (Hotspot).
    n_bins: number of confidence bins in [0.5, 1.0].
    """
    y_true = np.asarray(y_true).astype(int)
    probs = np.asarray(probs)
    
    # Confidence is max(p, 1-p) for binary classification, ranging in [0.5, 1.0]
    confidences = np.maximum(probs, 1.0 - probs)
    predictions = (probs >= 0.5).astype(int)
    accuracies = (predictions == y_true).astype(float)
    
    bin_edges = np.linspace(0.5, 1.0, n_bins + 1)
    bin_confs, bin_accs, bin_weights = [], [], []
    ece = 0.0
    mce = 0.0
    n_total = len(y_true)

    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            in_bin = (confidences >= low) & (confidences <= high)
        else:
            in_bin = (confidences >= low) & (confidences < high)

        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            weight = bin_size / n_total
            gap = abs(bin_acc - bin_conf)
            ece += weight * gap
            mce = max(mce, gap)
            bin_confs.append(bin_conf)
            bin_accs.append(bin_acc)
            bin_weights.append(bin_size)
        else:
            bin_confs.append((low + high) / 2.0)
            bin_accs.append(0.0)
            bin_weights.append(0)

    return {
        "ece": float(ece),
        "mce": float(mce),
        "bin_edges": bin_edges,
        "bin_confs": np.array(bin_confs),
        "bin_accs": np.array(bin_accs),
        "bin_counts": np.array(bin_weights),
    }

def plot_reliability_diagram(cal_dict, save_path, title="Reliability Diagram"):
    """Plots and saves an IEEE-quality Reliability Diagram."""
    bin_edges = cal_dict["bin_edges"]
    bin_accs = cal_dict["bin_accs"]
    bin_confs = cal_dict["bin_confs"]
    bin_counts = cal_dict["bin_counts"]
    ece = cal_dict["ece"]

    fig, ax1 = plt.subplots(figsize=(5, 4.5), dpi=300)
    
    # Perfect calibration reference
    ax1.plot([0.5, 1.0], [0.5, 1.0], "--", color="gray", label="Perfect Calibration")

    # Bar chart for bin accuracy
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    width = (bin_edges[1] - bin_edges[0]) * 0.85
    
    ax1.bar(bin_centers, bin_accs, width=width, alpha=0.6, color="#1f77b4", edgecolor="black", label="Empirical Accuracy")
    ax1.plot(bin_centers, bin_confs, "o-", color="#d62728", linewidth=1.5, label="Mean Confidence")

    ax1.set_xlabel("Confidence", fontsize=11)
    ax1.set_ylabel("Empirical Accuracy", fontsize=11)
    ax1.set_xlim([0.48, 1.02])
    ax1.set_ylim([0.0, 1.05])
    ax1.set_title(f"{title}\nECE = {ece:.3f}", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
