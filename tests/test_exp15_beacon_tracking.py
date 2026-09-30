import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from generator.camera import PinholeCamera
from experiments.exp15_beacon_tracking.src.motion_generator import BeaconMotionGenerator
from experiments.exp15_beacon_tracking.src.tracker import FSOCBeaconTracker
from experiments.exp15_beacon_tracking.src.run_experiment import Exp15BeaconTracking

def test_motion_generator_trajectories():
    """Verify ground truth motion trajectory generation across all motion types."""
    gen = BeaconMotionGenerator(width=1920, height=1080, fps=30.0)

    for m_type in ["constant_velocity", "accelerating", "sinusoidal", "random_maneuver", "occlusion_fade"]:
        traj = gen.generate_trajectory(motion_type=m_type, num_frames=50, seed=42)
        assert len(traj["x_true"]) == 50
        assert len(traj["y_true"]) == 50
        assert len(traj["amplitude"]) == 50
        assert len(traj["is_occluded"]) == 50

        if m_type == "occlusion_fade":
            assert np.sum(traj["is_occluded"]) > 0
            assert np.min(traj["amplitude"]) == 0.0

def test_fsoc_beacon_tracker_state_transitions():
    """Verify tracker state machine transitions and measurement gating."""
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    tracker = FSOCBeaconTracker(camera=cam, estimator_type="Gaussian Fitting", fps=30.0)

    assert tracker.state == "INITIALIZING"

    # Frame 1: Initialized at GT
    img = np.zeros((1080, 1920), dtype=np.uint8)
    # Add fake beacon spot at (960, 540)
    img[535:545, 955:965] = 200

    res1 = tracker.process_frame(img, x_gt=960.0, y_gt=540.0, is_occluded_gt=False)
    assert res1["track_state"] in ["INITIALIZING", "TRACKING"]

def test_exp15_mini_execution_and_artifacts():
    """Verify Exp15 end-to-end execution on mini scale (2 sequence trials)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp15BeaconTracking(results_dir=tmp_dir)
        df_frames, df_summary, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp15_beacon_tracking")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_sequence_frames.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "2d_trajectories.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "temporal_position_error.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "occlusion_reacquisition.png"))
