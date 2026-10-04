"""
Deterministic Unit Test for Predictive Ablation Debug Scenario (Priority 1E).
Verifies that all 6 predictive/search variants maintain valid search states
without NaN collapse on a simple straight-line scenario.
"""

import pytest
import numpy as np
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from processing.cascaded_tracker import FastCascadeFSOCBBeaconTracker
from experiments.exp15_beacon_tracking.src.motion_generator import BeaconMotionGenerator


def test_predictive_ablation_debug_scenario():
    """
    Priority 1E Debug Scenario:
    - 640x480 resolution
    - 4°x3° FOV
    - Straight-line target
    - Low noise (SNR = 25 dB)
    - No atmospheric disturbance, no jitter, no platform motion
    - Known seed
    - Target starts inside FOV (320, 240)
    """
    camera = PinholeCamera.from_fov(width=640, height=480, fov_x_deg=4.0, fov_y_deg=3.0, fps=30.0)
    generator = SyntheticBeaconGenerator(camera=camera)
    motion_gen = BeaconMotionGenerator(width=640, height=480, fps=30.0)

    num_frames = 50
    seed = 12345
    traj = motion_gen.generate_trajectory("straight_line", num_frames=num_frames, seed=seed)

    variants = ["fixed", "current", "predictive", "cov_shaped", "cov_nis", "cov_nis_horizon"]

    for code in variants:
        tracker = FastCascadeFSOCBBeaconTracker(camera=camera, fps=30.0)
        valid_meas_count = 0

        for k in range(num_frames):
            x_gt = float(traj["x_true"][k])
            y_gt = float(traj["y_true"][k])

            img, _ = generator.generate_frame(
                x0=x_gt, y0=y_gt, amplitude=200.0, sigma_x=2.0, sigma_y=2.0,
                psf_type="gaussian", background_type="uniform", background_level=10.0, snr_db=25.0, seed=seed * 100 + k
            )

            res = tracker.process_frame(frame=img, search_variant=code, frame_id=k)

            # Assert NO NaN collapse in predictions or search centers
            assert not np.isnan(res["x_pred"]), f"Variant {code} produced NaN x_pred at frame {k}"
            assert not np.isnan(res["y_pred"]), f"Variant {code} produced NaN y_pred at frame {k}"

            if res["measurement_valid"] and res["x_est"] is not None:
                valid_meas_count += 1
                assert not np.isnan(res["x_est"]), f"Variant {code} produced NaN x_est at frame {k}"
                assert not np.isnan(res["y_est"]), f"Variant {code} produced NaN y_est at frame {k}"

        # Assert every variant achieves >= 80% valid tracking in simple debug scenario
        track_ratio = valid_meas_count / float(num_frames)
        assert track_ratio >= 0.80, f"Variant {code} tracking ratio {track_ratio:.2f} < 0.80 in simple debug scenario!"
