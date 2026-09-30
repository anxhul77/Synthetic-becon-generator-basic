import os
import time
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from .ai_detector import BeaconHeatmapNet

def train_model(train_loader: DataLoader,
                val_loader: DataLoader,
                output_dir: str = "models/exp06",
                num_epochs: int = 15,
                learning_rate: float = 1e-3,
                device: str = "cpu") -> tuple[str, pd.DataFrame, pd.DataFrame]:
    """
    Trains BeaconHeatmapNet on train set, evaluates on validation set,
    and saves best checkpoint and loss history.
    """
    os.makedirs(output_dir, exist_ok=True)
    device_obj = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")

    model = BeaconHeatmapNet().to(device_obj)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    history_records = []
    val_records = []

    best_val_loss = float("inf")
    best_checkpoint_path = os.path.join(output_dir, "exp06_beacon_ai_model.pt")

    print(f"Starting AI model training for {num_epochs} epochs on device: {device_obj}...", flush=True)

    for epoch in range(1, num_epochs + 1):
        t0 = time.perf_counter()
        model.train()
        running_train_loss = 0.0
        train_batches = 0

        for images, targets, metas in train_loader:
            images = images.to(device_obj)
            targets = targets.to(device_obj)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_train_loss += loss.item()
            train_batches += 1

        train_loss = running_train_loss / max(1, train_batches)

        # Validation phase
        model.eval()
        running_val_loss = 0.0
        val_batches = 0
        with torch.no_grad():
            for images, targets, metas in val_loader:
                images = images.to(device_obj)
                targets = targets.to(device_obj)
                outputs = model(images)
                loss = criterion(outputs, targets)
                running_val_loss += loss.item()
                val_batches += 1

        val_loss = running_val_loss / max(1, val_batches)
        t1 = time.perf_counter()
        epoch_time_s = t1 - t0

        print(f"Epoch {epoch:02d}/{num_epochs:02d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | Time: {epoch_time_s:.2f}s", flush=True)

        history_records.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "epoch_time_s": epoch_time_s
        })

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_checkpoint_path)
            val_records.append({
                "epoch": epoch,
                "best_val_loss": best_val_loss,
                "checkpoint_path": best_checkpoint_path
            })

        if val_loss < 0.003 and epoch >= 3:
            print(f"Early stopping triggered at epoch {epoch} with val loss {val_loss:.6f} < 0.003.", flush=True)
            break

    df_history = pd.DataFrame(history_records)
    df_val = pd.DataFrame(val_records)

    df_history.to_csv(os.path.join(output_dir, "training_history.csv"), index=False)
    df_val.to_csv(os.path.join(output_dir, "validation_metrics.csv"), index=False)

    print(f"Model training complete. Best checkpoint saved to {best_checkpoint_path} with val loss {best_val_loss:.6f}.", flush=True)
    return best_checkpoint_path, df_history, df_val
