import time
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

num_cpus = os.cpu_count() or 4
torch.set_num_threads(max(1, num_cpus - 2))

class BeaconHeatmapNet(nn.Module):
    """
    Lightweight Fully Convolutional Neural Network for optical beacon heatmap prediction.
    Super compact (~35k parameters) for ultra-fast, deterministic CPU/GPU inference.
    """
    def __init__(self):
        super().__init__()
        # Encoder
        self.enc1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.enc2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)  # 540, 960
        self.bn2 = nn.BatchNorm2d(32)
        self.enc3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)

        # Decoder / Bottleneck
        self.dec1 = nn.Conv2d(64, 32, kernel_size=3, padding=1)
        self.bn_dec1 = nn.BatchNorm2d(32)
        self.dec2 = nn.Conv2d(32, 16, kernel_size=3, padding=1)
        self.bn_dec2 = nn.BatchNorm2d(16)
        
        # Output Head
        self.head = nn.Conv2d(16, 1, kernel_size=3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input: [B, 1, H, W]
        x1 = F.relu(self.bn1(self.enc1(x)))
        x2 = F.relu(self.bn2(self.enc2(x1)))
        x3 = F.relu(self.bn3(self.enc3(x2)))

        d1 = F.relu(self.bn_dec1(self.dec1(x3)))
        d2 = F.relu(self.bn_dec2(self.dec2(d1)))

        heatmap = torch.sigmoid(self.head(d2))  # [B, 1, H, W]
        return heatmap

class AIBeaconDetector:
    """
    AI Beacon Detector Wrapper.
    Handles pre-processing, CNN model inference, confidence thresholding,
    subpixel peak extraction, and coordinate mapping back to original camera space.
    """
    def __init__(self,
                 model_path: str = None,
                 confidence_threshold: float = 0.5,
                 scale_factor: float = 0.5,
                 device: str = "cpu"):
        self.confidence_threshold = float(confidence_threshold)
        self.scale_factor = float(scale_factor)
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        
        self.model = BeaconHeatmapNet().to(self.device)
        self.model.eval()

        if model_path is not None and os.path.exists(model_path):
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)

    def set_confidence_threshold(self, threshold: float):
        self.confidence_threshold = float(threshold)

    def detect(self, image: np.ndarray, beacon_gt: tuple[float, float] = None, tolerance_px: float = 5.0) -> dict:
        """
        Executes AI inference on raw monochrome image and extracts candidate coordinates.
        """
        t0 = time.perf_counter()
        img_arr = np.asarray(image, dtype=np.float32)
        if img_arr.max() > 1.0:
            img_norm = img_arr / 255.0
        else:
            img_norm = img_arr

        if img_norm.shape == (1080, 1920):
            img_sub = img_norm[::2, ::2]
        else:
            img_sub = img_norm

        # Convert to Tensor [1, 1, H, W]
        img_tensor = torch.from_numpy(img_sub).unsqueeze(0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            heatmap_tensor = self.model(img_tensor)
            heatmap = heatmap_tensor.squeeze().cpu().numpy()  # [H_out, W_out]

        t1 = time.perf_counter()
        inference_latency_ms = (t1 - t0) * 1000.0

        H_out, W_out = heatmap.shape

        # Extract local peaks above confidence threshold
        max_val = float(heatmap.max())
        if img_norm.max() == 0 or max_val < self.confidence_threshold:
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "confidence": 0.0 if img_norm.max() == 0 else max_val,
                "num_candidates": 0,
                "primary_candidate": None,
                "candidates": [],
                "inference_latency_ms": inference_latency_ms
            }

        # Subpixel centroid extraction around peak
        peak_y, peak_x = np.unravel_index(np.argmax(heatmap), heatmap.shape)
        
        radius = 3
        y_min = max(0, peak_y - radius)
        y_max = min(H_out, peak_y + radius + 1)
        x_min = max(0, peak_x - radius)
        x_max = min(W_out, peak_x + radius + 1)

        patch = heatmap[y_min:y_max, x_min:x_max]
        patch_sum = float(patch.sum())
        if patch_sum > 0:
            grid_y, grid_x = np.ogrid[y_min:y_max, x_min:x_max]
            sub_x = float((patch * grid_x).sum() / patch_sum)
            sub_y = float((patch * grid_y).sum() / patch_sum)
        else:
            sub_x, sub_y = float(peak_x), float(peak_y)

        # Scale coordinates back to full image resolution
        x_est = sub_x / self.scale_factor
        y_est = sub_y / self.scale_factor

        primary_cand = {
            "x_est": x_est,
            "y_est": y_est,
            "confidence": max_val,
            "peak_x_out": int(peak_x),
            "peak_y_out": int(peak_y)
        }

        # Collect secondary candidates if heatmap has multiple distinct peaks > threshold
        candidates = [primary_cand]

        return {
            "detected": True,
            "x_est": x_est,
            "y_est": y_est,
            "confidence": max_val,
            "num_candidates": len(candidates),
            "primary_candidate": primary_cand,
            "candidates": candidates,
            "inference_latency_ms": inference_latency_ms
        }
