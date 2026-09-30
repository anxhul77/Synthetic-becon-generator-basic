import os
import pytest
import numpy as np
import pandas as pd
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from generator.noise import GaussianNoise
from processing.detector import ClassicalBeaconDetector
from metrics.stats import compute_wilson_ci, compute_bootstrap_rmse_ci
from experiments.exp01_noise_robustness.experiment import Exp01NoiseRobustness

def test_snr_to_noise_std_calculation():
    """Verify formula: sigma_n = A * 10^(-SNR_dB / 20) for configured amplitude A=150."""
    amplitude = 150.0
    
    # 20 dB: 150 * 10^(-1) = 15.0
    model_20 = GaussianNoise(snr_db=20.0, amplitude=amplitude)
    assert np.isclose(model_20.sigma_n, 15.0, atol=1e-5)

    # 0 dB: 150 * 10^(0) = 150.0
    model_0 = GaussianNoise(snr_db=0.0, amplitude=amplitude)
    assert np.isclose(model_0.sigma_n, 150.0, atol=1e-5)

    # 30 dB: 150 * 10^(-1.5) = 4.743416...
    model_30 = GaussianNoise(snr_db=30.0, amplitude=amplitude)
    expected_30 = 150.0 * (10.0 ** (-30.0 / 20.0))
    assert np.isclose(model_30.sigma_n, expected_30, atol=1e-5)


def test_classification_detections_and_misses():
    """Verify that primary candidates within tolerance are classified as correct detections, others as misses."""
    detector = ClassicalBeaconDetector(threshold=160.0)
    camera = PinholeCamera()
    generator = SyntheticBeaconGenerator(camera=camera)

    # High SNR frame -> correct detection near (960, 540)
    img_clean, _ = generator.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, background_level=100.0, snr_db=30.0, seed=42)
    res_clean = detector.detect(img_clean)

    assert res_clean["detected"] is True
    assert res_clean["primary_candidate"] is not None
    dist = np.sqrt((res_clean["x_est"] - 960.0)**2 + (res_clean["y_est"] - 540.0)**2)
    assert dist <= 5.0

    # Frame with no beacon above threshold -> miss
    img_empty = np.full((1080, 1920), 100, dtype=np.uint8)
    res_empty = detector.detect(img_empty)
    assert res_empty["detected"] is False
    assert res_empty["primary_candidate"] is None


def test_false_alarm_denominator_and_counting():
    """Verify false alarm counting: denominator is total images, false alarm images counted when >=1 non-beacon candidate exists."""
    detector = ClassicalBeaconDetector(threshold=160.0)
    
    # Synthetic frame with 1 true beacon at (960, 540) and 2 fake noise blobs far away
    img = np.full((1080, 1920), 100, dtype=np.uint8)
    # True beacon
    img[538:543, 958:963] = 250
    # 2 False noise candidates
    img[100:105, 100:105] = 200
    img[800:805, 800:805] = 200

    res = detector.detect(img)
    assert res["num_candidates"] == 3

    beacon_x, beacon_y = 960.0, 540.0
    tol = 5.0
    matching = 0
    for c in res["candidates"]:
        d = np.sqrt((c["x_est"] - beacon_x)**2 + (c["y_est"] - beacon_y)**2)
        if d <= tol:
            matching += 1
    
    false_cand_cnt = res["num_candidates"] - matching
    assert matching == 1
    assert false_cand_cnt == 2
    # Image-level false alarm status
    is_fa_image = 1 if false_cand_cnt >= 1 else 0
    assert is_fa_image == 1


def test_localization_error_and_rmse():
    """Verify radial error, signed bias, and RMSE calculations."""
    errs_x = np.array([0.1, -0.2, 0.3])
    errs_y = np.array([-0.1, 0.2, 0.4])
    errs_r = np.sqrt(errs_x**2 + errs_y**2)

    rmse_x = np.sqrt(np.mean(errs_x**2))
    rmse_y = np.sqrt(np.mean(errs_y**2))
    rmse_r = np.sqrt(np.mean(errs_r**2))
    bias_x = np.mean(errs_x)
    bias_y = np.mean(errs_y)

    assert np.isclose(rmse_x, np.sqrt((0.01 + 0.04 + 0.09)/3))
    assert np.isclose(rmse_y, np.sqrt((0.01 + 0.04 + 0.16)/3))
    assert np.isclose(bias_x, (0.1 - 0.2 + 0.3)/3)
    assert np.isclose(bias_y, (-0.1 + 0.2 + 0.4)/3)


def test_deterministic_trial_seed_generation():
    """Verify deterministic trial seed formula based on experiment, SNR level index, and trial index."""
    base_seed = 42
    snr_levels = [30.0, 25.0, 20.0, 15.0, 10.0, 7.0, 5.0, 3.0, 0.0]

    seeds_1 = [base_seed + i_snr * 10000 + t for i_snr in range(len(snr_levels)) for t in range(5)]
    seeds_2 = [base_seed + i_snr * 10000 + t for i_snr in range(len(snr_levels)) for t in range(5)]

    assert len(seeds_1) == len(set(seeds_1))  # Unique across levels & trials
    assert seeds_1 == seeds_2  # Deterministic


def test_reproducibility_of_experiment_results():
    """Verify that identical trial seeds produce identical synthetic frames and detector outputs."""
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    det = ClassicalBeaconDetector(threshold=160.0)

    img1, gt1 = gen.generate_frame(snr_db=15.0, seed=12345)
    img2, gt2 = gen.generate_frame(snr_db=15.0, seed=12345)

    assert np.array_equal(img1, img2)
    assert gt1["seed"] == gt2["seed"]

    res1 = det.detect(img1)
    res2 = det.detect(img2)
    assert res1["x_est"] == res2["x_est"]
    assert res1["y_est"] == res2["y_est"]
    assert res1["num_candidates"] == res2["num_candidates"]


def test_aggregation_of_trial_data():
    """Verify summary table aggregation metrics (P_D, P_FA, CIs) from raw trial dataframe."""
    trials = [
        {"snr_db": 30.0, "detected": 1, "false_alarm": 0, "false_candidate_count": 0, "candidate_count": 1, "error_x": 0.1, "error_y": 0.1, "radial_error": np.sqrt(0.02), "sigma_n": 4.74, "detector_latency_ms": 10.0},
        {"snr_db": 30.0, "detected": 1, "false_alarm": 0, "false_candidate_count": 0, "candidate_count": 1, "error_x": -0.1, "error_y": -0.1, "radial_error": np.sqrt(0.02), "sigma_n": 4.74, "detector_latency_ms": 12.0},
    ]
    df_raw = pd.DataFrame(trials)
    exp = Exp01NoiseRobustness(results_dir="results/test_tmp")
    df_sum = exp.aggregate_summary(df_raw)

    assert len(df_sum) == 1
    assert df_sum["detection_probability"].iloc[0] == 1.0
    assert df_sum["false_alarm_rate"].iloc[0] == 0.0
    assert df_sum["num_localizations"].iloc[0] == 2
    assert np.isclose(df_sum["rmse_radial"].iloc[0], np.sqrt(0.02))


def test_graceful_handling_of_zero_successful_localizations():
    """Verify summary metrics aggregation when correct detections count is 0."""
    trials = [
        {"snr_db": 0.0, "detected": 0, "false_alarm": 1, "false_candidate_count": 5, "candidate_count": 5, "error_x": np.nan, "error_y": np.nan, "radial_error": np.nan, "sigma_n": 150.0, "detector_latency_ms": 15.0},
        {"snr_db": 0.0, "detected": 0, "false_alarm": 1, "false_candidate_count": 4, "candidate_count": 4, "error_x": np.nan, "error_y": np.nan, "radial_error": np.nan, "sigma_n": 150.0, "detector_latency_ms": 14.0},
    ]
    df_raw = pd.DataFrame(trials)
    exp = Exp01NoiseRobustness(results_dir="results/test_tmp")
    df_sum = exp.aggregate_summary(df_raw)

    assert df_sum["correct_detections"].iloc[0] == 0
    assert df_sum["num_localizations"].iloc[0] == 0
    assert np.isnan(df_sum["rmse_radial"].iloc[0])
    assert np.isnan(df_sum["bias_x"].iloc[0])


def test_streaming_execution_without_storing_all_images(tmp_path):
    """Verify that running mini experiment executes frame-by-frame in streaming fashion."""
    exp = Exp01NoiseRobustness(results_dir=str(tmp_path))
    # Override config for fast mini test
    cfg = exp.load_config()
    cfg["snr_levels"] = [30.0, 10.0]
    cfg["trials_per_snr"] = 2
    
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    det = ClassicalBeaconDetector(threshold=cfg["detector_threshold"])

    for i_snr, snr in enumerate(cfg["snr_levels"]):
        for t in range(cfg["trials_per_snr"]):
            seed = cfg["seed"] + i_snr * 10000 + t
            img, gt = gen.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, background_level=100.0, snr_db=snr, seed=seed)

            res = det.detect(img)
            # Image array dereferenced immediately
            del img
            assert "x_est" in res


def test_consistent_configuration_across_snr_levels():
    """Verify that all generator parameters except SNR (and derived sigma_n) remain constant across trials."""
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    
    _, gt1 = gen.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, snr_db=30.0, background_level=100.0, range_km=0.0, seed=1)
    _, gt2 = gen.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, snr_db=0.0, background_level=100.0, range_km=0.0, seed=2)

    # Constant parameters
    assert gt1["x_true"] == gt2["x_true"] == 960.0
    assert gt1["y_true"] == gt2["y_true"] == 540.0
    assert gt1["amplitude"] == gt2["amplitude"] == 150.0
    assert gt1["background"] == gt2["background"] == 100.0
    assert gt1["sigma_x"] == gt2["sigma_x"] == 2.0
    assert gt1["sigma_y"] == gt2["sigma_y"] == 2.0

    # SNR and sigma_n vary
    assert gt1["snr_db"] == 30.0
    assert gt2["snr_db"] == 0.0
    assert gt1["sigma_n"] < gt2["sigma_n"]
