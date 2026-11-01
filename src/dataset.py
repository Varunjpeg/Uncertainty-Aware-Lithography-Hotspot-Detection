import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, Subset

class HotspotCachedDataset(Dataset):
    """
    In-memory PyTorch Dataset for cached ICCAD layout crops.
    Input images: (N, 64, 64) uint8 -> (N, 1, 64, 64) float32 in [0, 1].
    Labels: 1 for Hotspot (HS), 0 for Non-Hotspot (NHS).
    """
    def __init__(self, images, labels, augment=False):
        self.images = images  # uint8 array of shape (N, H, W)
        self.labels = labels  # int64 array of shape (N,)
        self.augment = augment

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        img = self.images[idx]  # (H, W) uint8
        label = self.labels[idx]

        if self.augment and label == 1:
            # 8-fold Manhattan symmetry augmentation for minority hotspot patterns
            k = np.random.randint(0, 4)
            img = np.rot90(img, k)
            if np.random.rand() > 0.5:
                img = np.fliplr(img)
            if np.random.rand() > 0.5:
                img = np.flipud(img)

        # Normalize to [0.0, 1.0] float tensor with channel dimension (1, H, W)
        img_tensor = torch.from_numpy(np.ascontiguousarray(img)).float().unsqueeze(0) / 255.0
        label_tensor = torch.tensor(label, dtype=torch.float32)
        return img_tensor, label_tensor

def load_cached_benchmark(cache_dir, benchmark_name):
    """Loads pre-cached npz files for a specific benchmark."""
    train_path = f"{cache_dir}/{benchmark_name}_train.npz"
    test_path = f"{cache_dir}/{benchmark_name}_test.npz"
    train_data = np.load(train_path)
    test_data = np.load(test_path)
    return train_data['images'], train_data['labels'], test_data['images'], test_data['labels']

def get_stratified_train_val_loaders(train_images, train_labels, seed=42, val_fraction=0.20, batch_size=64):
    """
    Creates stratified train and validation loaders.
    Guarantees that rare Hotspots are represented in both splits.
    """
    rng = np.random.default_rng(seed)
    hs_idx = np.where(train_labels == 1)[0]
    nhs_idx = np.where(train_labels == 0)[0]
    
    rng.shuffle(hs_idx)
    rng.shuffle(nhs_idx)

    hs_val_count = max(1, int(round(len(hs_idx) * val_fraction)))
    nhs_val_count = max(1, int(round(len(nhs_idx) * val_fraction)))

    val_indices = np.concatenate([hs_idx[:hs_val_count], nhs_idx[:nhs_val_count]])
    train_indices = np.concatenate([hs_idx[hs_val_count:], nhs_idx[nhs_val_count:]])

    rng.shuffle(train_indices)
    rng.shuffle(val_indices)

    # Calculate positive class imbalance weight for BCEWithLogitsLoss
    train_hs_count = np.sum(train_labels[train_indices] == 1)
    train_nhs_count = np.sum(train_labels[train_indices] == 0)
    pos_weight = float(train_nhs_count) / max(1.0, float(train_hs_count))

    train_ds = HotspotCachedDataset(train_images[train_indices], train_labels[train_indices], augment=True)
    val_ds = HotspotCachedDataset(train_images[val_indices], train_labels[val_indices], augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, drop_last=False)

    return train_loader, val_loader, pos_weight, len(train_indices), len(val_indices)

def get_test_loader(test_images, test_labels, batch_size=128):
    """Creates DataLoader for official test set."""
    test_ds = HotspotCachedDataset(test_images, test_labels, augment=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, drop_last=False)
    return test_loader
