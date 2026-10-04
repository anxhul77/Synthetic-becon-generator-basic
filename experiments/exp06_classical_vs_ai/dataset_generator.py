import os
import json
import uuid
import numpy as np
import pandas as pd
from generator.generator import SyntheticBeaconGenerator
from generator.camera import PinholeCamera

class Exp06DatasetGenerator:
    """
    Dataset Generator for Experiment 6: Classical vs AI vs Hybrid Detection.
    
    Generates independent, leak-free Train (70%), Validation (15%), and Test (15%) splits
    with disjoint seed spaces, configurable distractor counts, beacon-free frames,
    and structured manifest output.
    """
    def __init__(self,
                 base_dir: str = "datasets/exp06",
                 camera: PinholeCamera = None,
                 width: int = 1920,
                 height: int = 1080):
        self.base_dir = base_dir
        self.camera = camera if camera is not None else PinholeCamera(width=width, height=height)
        self.generator = SyntheticBeaconGenerator(camera=self.camera)

    def generate_dataset(self,
                         num_train: int = 1400,
                         num_val: int = 300,
                         num_test: int = 300,
                         save_on_disk: bool = True) -> tuple[pd.DataFrame, dict]:
        """
        Generates full dataset splits with guaranteed disjoint seed spaces.
        
        Disjoint seed allocations:
          - Train: 100,000 + i
          - Val:   200,000 + i
          - Test:  300,000 + i
        """
        manifest_records = []
        splits = [
            ("train", num_train, 100000),
            ("val", num_val, 200000),
            ("test", num_test, 300000)
        ]

        # Ensure directory structures exist
        for split_name, _, _ in splits:
            os.makedirs(os.path.join(self.base_dir, "images", split_name), exist_ok=True)

        dataset_dict = {"train": [], "val": [], "test": []}

        snr_choices = [30.0, 20.0, 15.0, 10.0, 5.0]
        bg_choices = [0.0, 50.0, 100.0, 200.0, 500.0]
        gradient_types = ["uniform", "horizontal", "vertical", "twod"]
        distractor_counts = [0, 1, 3, 5]
        psf_types = ["gaussian", "elliptical"]

        for split_name, count, seed_base in splits:
            print(f"Generating {split_name} split ({count} images)...", flush=True)
            for i in range(count):
                seed = seed_base + i
                rng = np.random.default_rng(seed)

                # 75% beacon present, 25% beacon absent
                beacon_present = bool(rng.random() < 0.75)

                # Beacon parameters (random location respecting 20px guard band)
                if beacon_present:
                    x0 = float(rng.uniform(20.0, self.camera.width - 20.0))
                    y0 = float(rng.uniform(20.0, self.camera.height - 20.0))
                else:
                    x0, y0 = 960.0, 540.0

                amplitude = float(rng.uniform(100.0, 200.0))
                psf_type = rng.choice(psf_types)
                if psf_type == "elliptical":
                    sigma_x = float(rng.uniform(1.2, 3.0))
                    sigma_y = float(rng.uniform(1.2, 3.0))
                else:
                    s_val = float(rng.uniform(1.0, 3.5))
                    sigma_x, sigma_y = s_val, s_val

                snr_db = float(rng.choice(snr_choices))

                # Special out-of-distribution test conditions for test set
                if split_name == "test" and i % 10 == 0:
                    snr_db = 0.0  # 0 dB test stress condition

                bg_type = rng.choice(gradient_types)
                bg_level = float(rng.choice(bg_choices))
                grad_a, grad_b = 0.0, 0.0
                if bg_type == "horizontal":
                    # Configured gradient is total DN change across the
                    # sensor, while GradientBackground expects DN/pixel.
                    grad_a, grad_b = 100.0 / max(1, self.camera.width - 1), 0.0
                elif bg_type == "vertical":
                    grad_a, grad_b = 0.0, 100.0 / max(1, self.camera.height - 1)
                elif bg_type == "twod":
                    grad_a = 100.0 / max(1, self.camera.width - 1)
                    grad_b = 100.0 / max(1, self.camera.height - 1)

                # Distractors (false bright objects)
                n_dist = int(rng.choice(distractor_counts))
                distractor_list = []
                for d_idx in range(n_dist):
                    dx = float(rng.uniform(20.0, self.camera.width - 20.0))
                    dy = float(rng.uniform(20.0, self.camera.height - 20.0))
                    # Distractor intensity comparable to beacon
                    d_amp = float(rng.uniform(80.0, 180.0))
                    d_psf = rng.choice(psf_types)
                    distractor_list.append({
                        "x0": dx, "y0": dy, "amplitude": d_amp,
                        "sigma_x": float(rng.uniform(1.5, 3.0)),
                        "sigma_y": float(rng.uniform(1.5, 3.0)),
                        "psf_type": d_psf
                    })

                image_id = f"img_{split_name}_{i:06d}_s{seed}"

                img, gt = self.generator.generate_frame(
                    x0=x0, y0=y0, amplitude=amplitude,
                    sigma_x=sigma_x, sigma_y=sigma_y, psf_type=psf_type,
                    background_type=bg_type if bg_type != "uniform" else "uniform",
                    background_level=bg_level,
                    gradient_a=grad_a, gradient_b=grad_b,
                    snr_db=snr_db, seed=seed, image_id=image_id, bit_depth=8,
                    beacon_present=beacon_present, distractors=distractor_list
                )

                # Save frame image on disk
                img_path = os.path.join(self.base_dir, "images", split_name, f"{image_id}.npz")
                if save_on_disk:
                    np.savez_compressed(img_path, image=img)

                record = {
                    "image_id": image_id,
                    "split": split_name,
                    "seed": seed,
                    "image_path": img_path,
                    "width": self.camera.width,
                    "height": self.camera.height,
                    "beacon_present": beacon_present,
                    "x_true": x0 if beacon_present else np.nan,
                    "y_true": y0 if beacon_present else np.nan,
                    "amplitude": amplitude,
                    "sigma_x": sigma_x,
                    "sigma_y": sigma_y,
                    "psf_type": psf_type,
                    "snr_db": snr_db,
                    "background_level": bg_level,
                    "background_type": bg_type,
                    "gradient_a": grad_a,
                    "gradient_b": grad_b,
                    "distractor_count": len(distractor_list),
                    "distractor_json": json.dumps(distractor_list)
                }
                manifest_records.append(record)

        df_manifest = pd.DataFrame(manifest_records)
        manifest_path = os.path.join(self.base_dir, "dataset_manifest.csv")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        df_manifest.to_csv(manifest_path, index=False)
        print(f"Dataset manifest written to {manifest_path} ({len(df_manifest)} total samples).", flush=True)

        return df_manifest, {}
