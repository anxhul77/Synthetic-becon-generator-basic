import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from experiments.exp16_motion_framerate.src.angular_velocity import (
    angular_velocity_to_pixel_velocity,
    compute_interframe_displacement
)
from experiments.exp16_motion_framerate.src.run_experiment import Exp16MotionFramerate

def test_angular_velocity_conversion_math():
    """Verify angular velocity to pixel velocity and inter-frame displacement math."""
    # 1 deg/s at f=2000 px -> v = 2000 * tan(1 deg in rad) = 2000 * 0.017455 = 34.91 px/s
    v_px = angular_velocity_to_pixel_velocity(omega_deg_per_sec=1.0, focal_length_px=2000.0)
    assert np.isclose(v_px, 34.91, atol=0.2)

    # At 30 FPS: delta_s = 34.91 / 30 = 1.16 px/frame
    disp = compute_interframe_displacement(omega_deg_per_sec=1.0, fps=30.0, focal_length_px=2000.0)
    assert np.isclose(disp["delta_s_px_per_frame"], 1.16, atol=0.05)

def test_exp16_mini_execution_and_artifacts():
    """Verify Exp16 end-to-end execution on mini scale (2 trials/condition)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp16MotionFramerate(results_dir=tmp_dir)
        df_frames, df_grid, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp16_motion_framerate")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_frames.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "operational_grid_summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "operational_boundary_heatmap.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "rmse_theta_vs_omega.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "reacquisition_time_vs_omega.png"))
