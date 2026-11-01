import copy
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import balanced_accuracy_score, recall_score, precision_score, f1_score

def evaluate_loader(model, loader, device):
    """Evaluates model on loader, returning predicted probabilities and true labels."""
    model.eval()
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for x_batch, y_batch in loader:
            x_batch = x_batch.to(device)
            logits = model(x_batch)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(y_batch.numpy())

    return np.concatenate(all_probs), np.concatenate(all_labels)

def train_model(model, train_loader, val_loader, pos_weight=1.0, epochs=8, lr=1e-3, device="cpu", verbose=True):
    """
    Trains UncertaintyHotspotCNN with class-imbalance weighted BCEWithLogitsLoss.
    Saves and returns the model state that achieves the highest validation Balanced Accuracy.
    """
    model.to(device)
    pos_weight_tensor = torch.tensor([pos_weight], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_bal_acc = -1.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        n_samples = 0

        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(x_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(y_batch)
            n_samples += len(y_batch)

        scheduler.step()
        epoch_loss = total_loss / max(1, n_samples)

        # Evaluate on validation split
        val_probs, val_labels = evaluate_loader(model, val_loader, device)
        val_preds = (val_probs >= 0.5).astype(int)
        val_bal_acc = balanced_accuracy_score(val_labels, val_preds)
        val_recall = recall_score(val_labels, val_preds, zero_division=0)
        val_f1 = f1_score(val_labels, val_preds, zero_division=0)

        if val_bal_acc > best_val_bal_acc:
            best_val_bal_acc = val_bal_acc
            best_weights = copy.deepcopy(model.state_dict())

        if verbose:
            print(f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_loss:.4f} | Val BalAcc: {val_bal_acc*100:.2f}% | Val Rec: {val_recall*100:.2f}% | Val F1: {val_f1*100:.2f}%")

    if best_weights is not None:
        model.load_state_dict(best_weights)

    return model, best_val_bal_acc
