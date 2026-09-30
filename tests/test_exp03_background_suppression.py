import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from generator.background import GradientBackground
from processing.detector import ClassicalBeaconDetector
from processing.background_suppression import (
    apply_none,
    apply_gaussian_sub,
    apply_tophat,
    get_suppression_filter,
    SUPPRESSION_REGISTRY,
)
from experiments.exp03_background_suppression.experiment import Exp03BackgroundSuppression


@pytest.fixture
def sample_image():
    """Generates a synthetic 1920x1080 uint8 test frame with uniform background=100."""
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    img, gt = generator.generate_frame(
        x0=960.0, y0=540.0, amplitude=150.0, background_level=100.0, snr_db=15.0, seed=42
    )
    return img, gt


def test_no_suppression_exact_preservation(sample_image):
    """Verify 'none' filter preserves input image exactly."""
    img, _ = sample_image
    filtered = apply_none(img)
    np.testing.assert_array_equal(img, filtered, err_msg="'none' filter mutated input array")


def test_gaussian_subtraction_validity_and_positive_residual(sample_image):
    """Verify Gaussian subtraction outputs valid shape, uint8 dtype, and preserves positive beacon residual."""
    img, _ = sample_image
    filtered = apply_gaussian_sub(img, sigma=15.0)

    assert isinstance(filtered, np.ndarray)
    assert filtered.shape == (1080, 1920)
    assert filtered.dtype == np.uint8
    assert np.min(filtered) >= 0 and np.max(filtered) <= 255

    # Center pixel (around beacon peak 960, 540) should be positive
    beacon_peak_region = filtered[538:543, 958:963]
    assert np.max(beacon_peak_region) > 0, "Gaussian subtraction suppressed beacon peak completely"


def test_tophat_filtering_validity(sample_image):
    """Verify Morphological Top-Hat output validity and shape."""
    img, _ = sample_image
    filtered = apply_tophat(img, radius=7)

    assert isinstance(filtered, np.ndarray)
    assert filtered.shape == (1080, 1920)
    assert filtered.dtype == np.uint8
    assert np.min(filtered) >= 0 and np.max(filtered) <= 255


def test_paired_trial_image_identity():
    """Verify identical input image passed to all 3 methods in a paired trial."""
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    img, gt = generator.generate_frame(x0=960.0, y0=540.0, background_level=100.0, seed=777)

    methods = ["none", "gaussian_sub", "tophat"]
    outputs = []
    for m in methods:
        fn, p = get_suppression_filter(m)
        filtered = fn(img.copy(), **p)
        outputs.append(filtered)

    assert len(outputs) == 3
    # Baseline 'none' must match input image exactly
    np.testing.assert_array_equal(outputs[0], img)


def test_deterministic_reproducibility():
    """Verify identical seeds produce identical frames and suppression outputs."""
    camera = PinholeCamera(width=1920, height=1080)
    gen1 = SyntheticBeaconGenerator(camera=camera)
    gen2 = SyntheticBeaconGenerator(camera=camera)

    img1, _ = gen1.generate_frame(x0=960.0, y0=540.0, background_level=100.0, seed=123)
    img2, _ = gen2.generate_frame(x0=960.0, y0=540.0, background_level=100.0, seed=123)
    np.testing.assert_array_equal(img1, img2)

    for m in ["gaussian_sub", "tophat"]:
        fn, p = get_suppression_filter(m)
        f1 = fn(img1, **p)
        f2 = fn(img2, **p)
        np.testing.assert_array_equal(f1, f2)


def test_gradient_background_min_max_generation():
    """Verify linear gradient background generation produces intended min, max, and directional changes."""
    bg_model = GradientBackground(baseline=100.0, a=100.0 / 1919.0, b=50.0 / 1079.0)
    bg = bg_model.render(width=1920, height=1080)

    assert bg.shape == (1080, 1920)
    assert np.isclose(bg[0, 0], 100.0)
    assert np.isclose(bg[0, 1919], 200.0)
    assert np.isclose(bg[1079, 0], 150.0)
    assert np.isclose(bg[1079, 1919], 250.0)


def test_exp03_mini_run_and_paired_alignment():
    """Test Exp03 full execution on a mini scale (1 uniform level, 1 gradient, 5 trials/cond)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mini_cfg_path = os.path.join(tmp_dir, "mini_cfg.yaml")
        mini_cfg_data = {
            "exp03_background_suppression": {
                "name": "Mini Experiment 3",
                "snr_db": 15.0,
                "trials_per_condition": 5,
                "methods": ["none", "gaussian_sub", "tophat"],
                "uniform_levels": [100.0],
                "gradient_scenarios": {
                    "horizontal": {"b0": 100.0, "delta_x": 100.0, "delta_y": 0.0}
                },
                "image_width": 1920,
                "image_height": 1080,
                "amplitude": 150.0,
                "sigma_x": 2.0,
                "sigma_y": 2.0,
                "bit_depth": 8,
                "beacon_x": 960.0,
                "beacon_y": 540.0,
                "detector_threshold": 160.0,
                "localization_tolerance_px": 5.0,
                "seed": 42
            }
        }
        with open(mini_cfg_path, "w", encoding="utf-8") as f:
            import yaml
            yaml.dump(mini_cfg_data, f)

        exp = Exp03BackgroundSuppression(config_file=mini_cfg_path, results_dir=tmp_dir)
        df_summary, df_paired, report_md = exp.run()

        assert os.path.exists(os.path.join(exp.exp_results_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "paired_comparison.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "experiment_report.md"))

        df_raw = pd.read_csv(os.path.join(exp.exp_results_dir, "raw_data.csv"))
        # 2 conditions (1 uniform + 1 gradient) x 5 trials x 3 methods = 30 evaluations
        assert len(df_raw) == 30

        # Every image_id must have exactly 3 method evaluations
        img_counts = df_raw.groupby("image_id").size()
        assert np.all(img_counts == 3)

        # PD and PFA must be within [0, 1]
        assert np.all((df_summary["detection_probability"] >= 0.0) & (df_summary["detection_probability"] <= 1.0))
        assert np.all((df_summary["false_alarm_rate_pfa"] >= 0.0) & (df_summary["false_alarm_rate_pfa"] <= 1.0))


def test_zero_successful_localizations_null_rmse_handling():
    """Verify zero successful localizations sets RMSE to NaN/null gracefully."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp03BackgroundSuppression(results_dir=tmp_dir)

        raw_rows = []
        for cond in ["uniform_b1000"]:
            for t in range(3):
                img_id = f"img_{cond}_t{t}"
                for m in ["none", "gaussian_sub", "tophat"]:
                    raw_rows.append({
                        "experiment_id": "exp03_background_suppression",
                        "scenario_id": cond,
                        "background_type": "uniform",
                        "background_level": 1000.0,
                        "gradient_x": 0.0,
                        "gradient_y": 0.0,
                        "snr_db": 15.0,
                        "trial": t + 1,
                        "seed": 42 + t,
                        "image_id": img_id,
                        "method": m,
                        "filter_params": "{}",
                        "beacon_x": 960.0,
                        "beacon_y": 540.0,
                        "detected": 0,
                        "estimated_x": np.nan,
                        "estimated_y": np.nan,
                        "localization_error_px": np.nan,
                        "error_x": np.nan,
                        "error_y": np.nan,
                        "false_candidate_count": 0,
                        "false_alarm": 0,
                        "candidate_count": 0,
                        "background_min": 1000.0,
                        "background_max": 1000.0,
                        "saturated_pixel_fraction": 1.0,
                        "sigma_n": 15.0,
                        "filter_latency_ms": 1.0,
                        "detector_latency_ms": 2.0,
                        "total_latency_ms": 3.0,
                        "successful_localization": 0
                    })
        df_raw = pd.DataFrame(raw_rows)
        df_summary = exp.aggregate_summary(df_raw)
        df_paired = exp.aggregate_paired_comparison(df_raw)

        assert np.all(np.isnan(df_summary["rmse_radial"]))
        assert np.all(df_paired["paired_successful_localizations"] == 0)
        assert np.all(np.isnan(df_paired["mean_radial_error_diff_px"]))
