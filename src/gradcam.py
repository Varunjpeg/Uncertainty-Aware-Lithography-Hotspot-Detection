import numpy as np
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt

class GradCAM:
    """
    Computes Gradient-weighted Class Activation Mapping (Grad-CAM)
    on the final convolutional layer of UncertaintyHotspotCNN.
    """
    def __init__(self, model):
        self.model = model
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        # Register hook on conv3 (last convolutional layer)
        self.model.conv3.register_forward_hook(forward_hook)
        self.model.conv3.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor):
        """
        Generates Grad-CAM heatmap for a single image tensor of shape (1, 1, H, W).
        Returns: (H, W) numpy array normalized to [0, 1].
        """
        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        logit = self.model(input_tensor)
        
        # Target logit backward
        logit.backward()

        # Global average pooling of gradients
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        activations = self.activations[0]  # (64, H_feat, W_feat)

        for i in range(activations.shape[0]):
            activations[i] *= pooled_gradients[i]

        heatmap = torch.mean(activations, dim=0).squeeze()
        heatmap = F.relu(heatmap)
        
        if torch.max(heatmap) > 0:
            heatmap /= torch.max(heatmap)

        # Upsample heatmap to match input dimensions (H, W)
        heatmap = F.interpolate(
            heatmap.unsqueeze(0).unsqueeze(0),
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode="bilinear",
            align_corners=False
        ).squeeze().detach().cpu().numpy()

        return heatmap

def quantify_gradcam_explanations(model, hs_loader, device="cpu", core_box=(16, 48, 16, 48), top_k_ratio=0.20):
    """
    Quantifies Grad-CAM on true hotspot samples using:
      1. Pointing Game Hit Rate (% of peak activations in core defect zone)
      2. Core Energy Concentration Ratio
      3. Faithfulness / Saliency Deletion Score (% drop in logit when salient features are masked)
    """
    gradcam = GradCAM(model)
    model.eval()

    total_hs = 0
    pointing_hits = 0
    core_energies = []
    cam_prob_drops = []
    random_prob_drops = []

    ymin, ymax, xmin, xmax = core_box

    for x_batch, y_batch in hs_loader:
        for i in range(len(y_batch)):
            if y_batch[i].item() != 1:
                continue

            img = x_batch[i:i+1].to(device)
            total_hs += 1

            # 1. Generate Heatmap
            heatmap = gradcam.generate_heatmap(img)
            
            # Pointing Game: check if peak activation falls in defect core
            peak_y, peak_x = np.unravel_index(np.argmax(heatmap), heatmap.shape)
            if ymin <= peak_y <= ymax and xmin <= peak_x <= xmax:
                pointing_hits += 1

            # Energy concentration ratio
            total_energy = np.sum(heatmap)
            core_energy = np.sum(heatmap[ymin:ymax, xmin:xmax])
            if total_energy > 0:
                core_energies.append(core_energy / total_energy)

            # 2. Faithfulness / Deletion Evaluation
            with torch.no_grad():
                base_prob = torch.sigmoid(model(img)).item()

                # Mask top_k salient pixels
                flat_cam = heatmap.flatten()
                threshold = np.percentile(flat_cam, (1.0 - top_k_ratio) * 100.0)
                mask = torch.tensor(heatmap < threshold, dtype=torch.float32, device=device).unsqueeze(0).unsqueeze(0)
                cam_masked_img = img * mask
                cam_masked_prob = torch.sigmoid(model(cam_masked_img)).item()
                cam_prob_drops.append(base_prob - cam_masked_prob)

                # Mask random top_k pixels
                rand_mask = torch.ones_like(img)
                n_pixels = img.shape[2] * img.shape[3]
                rand_indices = np.random.choice(n_pixels, int(n_pixels * top_k_ratio), replace=False)
                rand_mask.view(-1)[rand_indices] = 0.0
                rand_masked_img = img * rand_mask
                rand_masked_prob = torch.sigmoid(model(rand_masked_img)).item()
                random_prob_drops.append(base_prob - rand_masked_prob)

            if total_hs >= 100:  # evaluate on up to 100 HS samples for speed and consistency
                break
        if total_hs >= 100:
            break

    hit_rate = pointing_hits / max(1, total_hs)
    mean_core_energy = float(np.mean(core_energies)) if core_energies else 0.0
    mean_cam_drop = float(np.mean(cam_prob_drops)) if cam_prob_drops else 0.0
    mean_random_drop = float(np.mean(random_prob_drops)) if random_prob_drops else 0.0

    return {
        "evaluated_hs_count": total_hs,
        "pointing_game_hit_rate": hit_rate,
        "core_energy_ratio": mean_core_energy,
        "gradcam_deletion_prob_drop": mean_cam_drop,
        "random_deletion_prob_drop": mean_random_drop,
        "faithfulness_gain": mean_cam_drop - mean_random_drop,
    }

def plot_gradcam_overlay(image_np, heatmap, save_path, title="Grad-CAM Hotspot Localization"):
    """Saves visual overlay comparing original layout crop and Grad-CAM heatmap."""
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), dpi=300)
    
    # Raw layout
    axes[0].imshow(image_np, cmap="gray")
    axes[0].set_title("Input Layout Pattern", fontsize=10)
    axes[0].axis("off")

    # Heatmap
    axes[1].imshow(heatmap, cmap="jet")
    axes[1].set_title("Grad-CAM Saliency", fontsize=10)
    axes[1].axis("off")

    # Overlay
    axes[2].imshow(image_np, cmap="gray")
    im = axes[2].imshow(heatmap, cmap="jet", alpha=0.55)
    axes[2].set_title("Overlay (Vulnerable Region)", fontsize=10)
    axes[2].axis("off")

    plt.suptitle(title, fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
