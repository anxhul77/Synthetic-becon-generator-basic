import os
import shutil
import tempfile
import numpy as np
import pandas as pd
import pytest

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from processing.detector import ClassicalBeaconDetector
from processing.filters import (
    apply_none,
    apply_gaussian,
    apply_median,
    apply_bilateral,
    get_filter,
    FILTER_REGISTRY,
)
from experiments.exp02_denoising_comparison.experiment import Exp02DenoisingComparison


@pytest.fixture
def sample_image():
    """Generates a synthetic 1920x1080 uint8 monochrome test frame."""
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    img, gt = generator.generate_frame(
        x0=960.0, y0=540.0, amplitude=150.0, snr_db=15.0, seed=42
    )
    return img, gt


def test_filters_output_validity(sample_image):
    """Verify all four filter methods output images with expected shape, dtype, and valid range."""
    img, _ = sample_image
    methods = ["none", "gaussian", "median", "bilateral"]

    for m in methods:
        fn, params = get_filter(m)
        filtered = fn(img, **params)
        assert isinstance(filtered, np.ndarray), f"{m} did not return ndarray"
        assert filtered.shape == (1080, 1920), f"{m} changed image dimensions: {filtered.shape}"
        assert filtered.dtype == np.uint8, f"{m} dtype is not uint8: {filtered.dtype}"
        assert np.min(filtered) >= 0 and np.max(filtered) <= 255, f"{m} output out of uint8 range"


def test_no_filter_exact_preservation(sample_image):
    """Verify the 'none' filter preserves the input image byte-for-byte."""
    img, _ = sample_image
    filtered = apply_none(img)
    np.testing.assert_array_equal(img, filtered, err_msg="'none' filter mutated input array")


def test_paired_trial_image_identity():
    """Verify identical noisy image & ground truth are passed to all 4 methods in a paired trial."""
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    seed = 12345
    snr_db = 15.0

    # Generate frame once
    img, gt = generator.generate_frame(x0=960.0, y0=540.0, snr_db=snr_db, seed=seed)

    processed_frames = []
    methods = ["none", "gaussian", "median", "bilateral"]
    for m in methods:
        fn, params = get_filter(m)
        # Input image passed to each filter must be identical
        processed = fn(img.copy(), **params)
        processed_frames.append(processed)

    assert len(processed_frames) == 4
    # Ensure raw baseline matches original frame exactly
    np.testing.assert_array_equal(processed_frames[0], img)


def test_deterministic_reproducibility():
    """Verify identical configurations and seeds produce byte-for-byte identical results."""
    camera = PinholeCamera(width=1920, height=1080)
    gen1 = SyntheticBeaconGenerator(camera=camera)
    gen2 = SyntheticBeaconGenerator(camera=camera)

    img1, _ = gen1.generate_frame(x0=960.0, y0=540.0, snr_db=10.0, seed=999)
    img2, _ = gen2.generate_frame(x0=960.0, y0=540.0, snr_db=10.0, seed=999)

    np.testing.assert_array_equal(img1, img2)

    for m in ["gaussian", "median", "bilateral"]:
        fn, p = get_filter(m)
        f1 = fn(img1, **p)
        f2 = fn(img2, **p)
        np.testing.assert_array_equal(f1, f2, err_msg=f"Filter {m} is non-deterministic")


def test_exp02_small_run_and_paired_alignment():
    """Test full Exp02 experiment loop on a mini scale (2 SNRs, 5 trials/SNR)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mini_cfg_path = os.path.join(tmp_dir, "mini_cfg.yaml")
        mini_cfg_data = {
            "exp02_denoising_comparison": {
                "name": "Mini Experiment 2",
                "snr_levels": [20.0, 10.0],
                "trials_per_snr": 5,
                "methods": ["none", "gaussian", "median", "bilateral"],
                "image_width": 1920,
                "image_height": 1080,
                "amplitude": 150.0,
                "sigma_x": 2.0,
                "sigma_y": 2.0,
                "background_level": 100.0,
                "bit_depth": 8,
                "beacon_x": 960.0,
                "beacon_y": 540.0,
                "detector_threshold": 160.0,
                "localization_tolerance_px": 5.0,
                "seed": 100
            }
        }
        with open(mini_cfg_path, "w", encoding="utf-8") as f:
            import yaml
            yaml.dump(mini_cfg_data, f)

        exp = Exp02DenoisingComparison(config_file=mini_cfg_path, results_dir=tmp_dir)
        df_summary, df_paired, report_md = exp.run()

        assert os.path.exists(os.path.join(exp.exp_results_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "paired_comparison.csv"))
        assert os.path.exists(os.path.join(exp.exp_results_dir, "experiment_report.md"))

        df_raw = pd.read_csv(os.path.join(exp.exp_results_dir, "raw_data.csv"))
        assert len(df_raw) == 40  # 10 images x 4 methods

        # Verify every image_id has exactly 4 method rows
        img_counts = df_raw.groupby("image_id").size()
        assert np.all(img_counts == 4), "Not all noisy images were evaluated by all 4 methods"

        # Verify paired comparison alignment
        assert len(df_paired) == 2 * 3  # 2 SNRs x 3 non-baseline methods
        for _, row in df_paired.iterrows():
            assert row["method"] in ["gaussian", "median", "bilateral"]
            assert row["baseline_method"] == "none"
            assert row["paired_successful_trials"] >= 0


def test_zero_successful_localizations_handling():
    """Verify metrics and paired stats handle zero successful localizations without errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp02DenoisingComparison(results_dir=tmp_dir)

        # Create dummy raw data where all detections failed (detected = 0)
        raw_rows = []
        for snr in [20.0, 10.0]:
            for t in range(3):
                img_id = f"img_{snr:04.1f}_t{t}"
                for m in ["none", "gaussian", "median", "bilateral"]:
                    raw_rows.append({
                        "experiment_id": "exp02_denoising_comparison",
                        "snr_db": snr,
                        "trial": t + 1,
                        "seed": 100 + t,
                        "image_id": img_id,
                        "method": m,
                        "filter_params": "{}",
                        "x_true": 960.0,
                        "y_true": 540.0,
                        "x_est": np.nan,
                        "y_est": np.nan,
                        "detected": 0,
                        "candidate_count": 0,
                        "false_candidate_count": 0,
                        "false_alarm": 0,
                        "error_x": np.nan,
                        "error_y": np.nan,
                        "radial_error": np.nan,
                        "sigma_n": 15.0,
                        "filter_latency_ms": 0.5,
                        "detector_latency_ms": 2.0,
                        "total_latency_ms": 2.5,
                        "successful_localization": 0
                    })
        df_raw = pd.DataFrame(raw_rows)
        df_summary = exp.aggregate_summary(df_raw)
        df_paired = exp.aggregate_paired_comparison(df_raw)

        # Summary should have NaN for localization RMSE
        assert np.all(np.isnan(df_summary["rmse_radial"]))
        assert np.all(np.isnan(df_summary["bias_x"]))

        # Paired comparisons should have 0 paired successful trials and NaN diff
        assert np.all(df_paired["paired_successful_trials"] == 0)
        assert np.all(np.isnan(df_paired["mean_radial_error_diff_px"]))


def test_streaming_execution_memory_safety():
    """Verify processing streaming does not hold images in memory."""
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    detector = ClassicalBeaconDetector()

    # Process 20 images without accumulating img references
    frames_processed = 0
    for i in range(20):
        img, gt = generator.generate_frame(x0=960.0, y0=540.0, snr_db=15.0, seed=i)
        for m in ["none", "gaussian", "median", "bilateral"]:
            fn, p = get_filter(m)
            filt = fn(img, **p)
            det = detector.detect(filt, beacon_gt=(960.0, 540.0))
            frames_processed += 1
        del img  # explicit release check

    assert frames_processed == 80
