import torch
import torch.nn as nn
import torch.nn.functional as F

class UncertaintyHotspotCNN(nn.Module):
    """
    Lightweight, calibrated Convolutional Neural Network for Lithography Hotspot Detection.
    Features:
      - 3 Conv blocks with BatchNorm, ReLU, MaxPool, and spatial/standard Dropout.
      - Adaptive Average Pooling to prevent parameter explosion.
      - MC-Dropout support during inference.
      - Dedicated hook point on final conv layer for Grad-CAM explainability.
    Total parameters: ~40k (compact, fast CPU inference, resists overfitting).
    """
    def __init__(self, dropout_rate=0.25):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((2, 2))
        self.dropout_conv = nn.Dropout2d(dropout_rate)
        
        self.fc1 = nn.Linear(64 * 2 * 2, 64)
        self.dropout_fc = nn.Dropout(0.35)
        self.fc2 = nn.Linear(64, 1)

    def extract_features(self, x):
        """Passes input through convolutional stages, preserving conv3 feature map for Grad-CAM."""
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.dropout_conv(x)
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.dropout_conv(x)
        x = F.relu(self.bn3(self.conv3(x)))
        return x

    def forward(self, x):
        feat = self.extract_features(x)
        pooled = self.adaptive_pool(feat)
        flattened = torch.flatten(pooled, 1)
        h = F.relu(self.fc1(flattened))
        h = self.dropout_fc(h)
        logit = self.fc2(h).squeeze(-1)
        return logit

    def enable_mc_dropout(self):
        """
        Enables MC-Dropout during inference:
        Keeps Dropout active while keeping BatchNorm in evaluation mode (using running stats).
        """
        self.eval()
        for m in self.modules():
            if isinstance(m, (nn.Dropout, nn.Dropout2d)):
                m.train()
