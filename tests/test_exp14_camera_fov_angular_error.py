import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from generator.camera import PinholeCamera
from experiments.exp14_camera_fov_angular_error.src.angular_evaluation import (
    compute_exact_angular_pointing_error,
    compute_fov_metrics,
    compute_off_axis_scale_factor
)
from experiments.exp14_camera_fov_angular_error.src.run_experiment import Exp14CameraFOVAngularError

def test_fov_and_angular_error_math():
    """Verify exact arctan angular conversion equations and FOV calculations."""
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)

    res = compute_exact_angular_pointing_error(x_est=961.0, y_est=540.0, x_true=960.0, y_true=540.0, camera=cam)
    assert res["angular_error_urad"] is not None
    # 1 pixel at fx=2000 px is arctan(1/2000) rad = 0.0005 rad = 500 urad
    assert np.isclose(res["angular_error_urad"], 500.0, atol=1.0)

    fov_info = compute_fov_metrics(cam)
    assert np.isclose(fov_info["fov_x_deg"], 51.3, atol=0.5)
    assert np.isclose(fov_info["scale_center_urad_per_px"], 500.0)

def test_focal_length_scaling_properties():
    """Verify angular error scales inversely with focal length (e_theta = e_r / f)."""
    cam_wide = PinholeCamera(width=1920, height=1080, fx=500.0, fy=500.0, cx=960.0, cy=540.0)
    cam_tele = PinholeCamera(width=1920, height=1080, fx=8000.0, fy=8000.0, cx=960.0, cy=540.0)

    res_w = compute_exact_angular_pointing_error(x_est=960.5, y_est=540.0, x_true=960.0, y_true=540.0, camera=cam_wide)
    res_t = compute_exact_angular_pointing_error(x_est=960.5, y_est=540.0, x_true=960.0, y_true=540.0, camera=cam_tele)

    # 0.5 px error at fx=500 -> 1000 urad; at fx=8000 -> 62.5 urad
    assert res_w["angular_error_urad"] > res_t["angular_error_urad"] * 15.0
    assert np.isclose(res_w["angular_error_urad"] / res_t["angular_error_urad"], 16.0, atol=0.2)

def test_paired_estimator_evaluation():
    """Verify all 3 estimators receive identical generated frames per trial."""
    exp = Exp14CameraFOVAngularError()
    records, meta = exp.run_trial_image(
        trial_id="t001", seed=42, scenario_id="s1", sub_exp_id="sub1",
        x0=960.2, y0=540.3, focal_length=2000.0, snr_db=15.0
    )

    assert len(records) == 3
    methods = [r["method"] for r in records]
    assert "Intensity-Weighted Centroid" in methods
    assert "Gaussian Fitting" in methods
    assert "PSF Fitting" in methods

    for r in records:
        assert r["focal_length_px"] == 2000.0
        assert r["theta_x_true_rad"] == records[0]["theta_x_true_rad"]

def test_exp14_mini_execution_and_artifacts():
    """Verify Exp14 execution end-to-end on mini scale (2 trials/condition)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp14CameraFOVAngularError(results_dir=tmp_dir)
        df_summary, df_fov_summary, df_paired, df_raw, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp14_camera_fov_angular_error")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "fov_angular_summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "paired_comparison.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "angular_rmse_vs_focal_length.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "pixel_vs_angular_error_comparison.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "fov_vs_angular_precision.png"))
