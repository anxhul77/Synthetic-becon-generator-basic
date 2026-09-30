import os
import json
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

class BeaconDataset(Dataset):
    """
    PyTorch Dataset wrapper for synthetic FSOC beacon images.
    Returns:
      - image_tensor: FloatTensor of shape [1, H, W] in range [0, 1]
      - target_heatmap: FloatTensor of shape [1, H_out, W_out] in range [0, 1]
      - metadata_dict
    """
    def __init__(self,
                 manifest_df: pd.DataFrame,
                 scale_factor: float = 0.5,
                 heatmap_sigma: float = 2.0):
        self.df = manifest_df.reset_index(drop=True)
        self.scale_factor = scale_factor
        self.heatmap_sigma = heatmap_sigma

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = str(row["image_path"])

        if os.path.exists(img_path):
            data = np.load(img_path)
            img_full = data["image"].astype(np.float32) / 255.0
            img_arr = img_full[::2, ::2]
        else:
            # Fallback zero array if path missing
            img_arr = np.zeros((540, 960), dtype=np.float32)

        H, W = img_arr.shape
        H_out = H
        W_out = W

        target_hm = np.zeros((H_out, W_out), dtype=np.float32)

        beacon_present = bool(row["beacon_present"])
        if beacon_present and not np.isnan(row["x_true"]) and not np.isnan(row["y_true"]):
            x_true = float(row["x_true"]) * self.scale_factor
            y_true = float(row["y_true"]) * self.scale_factor

            # Render 2D Gaussian around target
            radius = int(np.ceil(3.0 * self.heatmap_sigma))
            cx, cy = int(round(x_true)), int(round(y_true))
            x_min = max(0, cx - radius)
            x_max = min(W_out, cx + radius + 1)
            y_min = max(0, cy - radius)
            y_max = min(H_out, cy + radius + 1)

            grid_x, grid_y = np.meshgrid(np.arange(x_min, x_max), np.arange(y_min, y_max))
            dist_sq = (grid_x - x_true) ** 2 + (grid_y - y_true) ** 2
            patch = np.exp(-dist_sq / (2.0 * self.heatmap_sigma ** 2))
            target_hm[y_min:y_max, x_min:x_max] = np.maximum(target_hm[y_min:y_max, x_min:x_max], patch)

        # Convert to PyTorch Tensors
        image_tensor = torch.from_numpy(img_arr).unsqueeze(0)        # [1, H, W]
        target_tensor = torch.from_numpy(target_hm).unsqueeze(0)      # [1, H_out, W_out]

        meta = {
            "image_id": str(row["image_id"]),
            "split": str(row["split"]),
            "beacon_present": beacon_present,
            "x_true": float(row["x_true"]) if beacon_present else float("nan"),
            "y_true": float(row["y_true"]) if beacon_present else float("nan"),
            "snr_db": float(row["snr_db"]),
            "background_level": float(row["background_level"]),
            "background_type": str(row["background_type"])
        }

        return image_tensor, target_tensor, meta

def create_dataloaders(manifest_df: pd.DataFrame,
                       batch_size: int = 8,
                       scale_factor: float = 0.5) -> dict[str, DataLoader]:
    """
    Creates DataLoaders for Train, Validation, and Test splits.
    """
    dataloaders = {}
    for split_name in ["train", "val", "test"]:
        sub_df = manifest_df[manifest_df["split"] == split_name]
        if len(sub_df) > 0:
            dataset = BeaconDataset(sub_df, scale_factor=scale_factor)
            shuffle = (split_name == "train")
            dataloaders[split_name] = DataLoader(
                dataset,
                batch_size=batch_size if split_name == "train" else 1,
                shuffle=shuffle,
                num_workers=0
            )
    return dataloaders
