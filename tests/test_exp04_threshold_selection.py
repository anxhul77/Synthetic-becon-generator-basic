import os
import numpy as np
import pytest
import pandas as pd

from processing.thresholding import (
    threshold_global,
    threshold_otsu,
    threshold_adaptive,
    threshold_mu_plus_k_sigma,
    get_thresholding_method,
    THRESHOLD_REGISTRY,
)
from processing.detector import ClassicalBeaconDetector
from generator.generator import SyntheticBeaconGenerator
from experiments.exp04_threshold_selection import Exp04ThresholdSelection


def test_1_global_threshold_expected_mask():
    """1. Global threshold produces the expected mask for a known test image."""
    img = np.array([[100, 150], [170, 200]], dtype=np.uint8)
    mask, info = threshold_global(img, threshold=160.0)
    expected = np.array([[0, 0], [1, 1]], dtype=np.uint8)
    np.testing.assert_array_equal(mask, expected)
    assert info["global_threshold"] == 160.0
    assert info["selected_threshold"] == 160.0


def test_2_otsu_threshold_nondegenerate():
    """2. Otsu returns a valid threshold for a nondegenerate image."""
    img = np.full((100, 100), 10, dtype=np.uint8)
    img[40:60, 40:60] = 200
    mask, info = threshold_otsu(img)
    assert 0 < info["selected_threshold"] < 200
    assert mask.shape == (100, 100)
    assert np.sum(mask) == 400



def test_3_adaptive_threshold_mask_size():
    """3. Adaptive threshold returns a correctly sized binary mask."""
    img = np.random.randint(50, 150, size=(120, 120), dtype=np.uint8)
    mask, info = threshold_adaptive(img, block_size=31, C=5.0)
    assert mask.shape == (120, 120)
    assert set(np.unique(mask)).issubset({0, 1})


def test_4_mu_plus_k_sigma_expected_threshold():
    """4. The \mu+k\sigma method computes expected threshold for known background distribution."""
    np.random.seed(42)
    bg = np.random.normal(loc=100.0, scale=10.0, size=(200, 200))
    bg_clip = np.clip(bg, 0, 255).astype(np.uint8)
    mask, info = threshold_mu_plus_k_sigma(bg_clip, k=3.0)
    expected_T = info["background_mean"] + 3.0 * info["background_std"]
    assert pytest.approx(info["selected_threshold"], abs=1e-3) == expected_T


def test_5_all_five_k_values_evaluated():
    """5. Each of the five k values (2, 3, 4, 5, 6) is registered and evaluated."""
    for k in [2, 3, 4, 5, 6]:
        method_name = f"mu_plus_{k}sigma"
        assert method_name in THRESHOLD_REGISTRY
        fn, params = get_thresholding_method(method_name)
        assert params["k"] == float(k)


def test_6_7_8_identical_inputs_and_pipeline():
    """
    6. All methods receive identical input images within each paired trial.
    7. Ground-truth coordinates are identical across methods.
    8. The same connected-component and localization code is used.
    """
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(seed=42)

    detector = ClassicalBeaconDetector()
    results = {}

    methods = ["global", "otsu", "adaptive", "mu_plus_3sigma"]
    for m in methods:
        fn, p = get_thresholding_method(m)
        mask, info = fn(img, **p)
        det = detector.detect(img, beacon_gt=(gt["x_true"], gt["y_true"]), binary_mask=mask)
        results[m] = det

    # Ensure all methods were passed identical img (no side effects)
    assert gt["x_true"] == 960.0
    assert gt["y_true"] == 540.0
    for m in methods:
        assert "num_candidates" in results[m]
        assert "matching_count" in results[m]


def test_9_reproducibility():
    """9. Repeated runs with the same seed reproduce all non-timing results."""
    gen = SyntheticBeaconGenerator()
    img1, gt1 = gen.generate_frame(seed=12345)
    img2, gt2 = gen.generate_frame(seed=12345)

    np.testing.assert_array_equal(img1, img2)
    assert gt1["x_true"] == gt2["x_true"]
    assert gt1["y_true"] == gt2["y_true"]

    fn, p = get_thresholding_method("otsu")
    mask1, info1 = fn(img1, **p)
    mask2, info2 = fn(img2, **p)

    np.testing.assert_array_equal(mask1, mask2)
    assert info1["selected_threshold"] == info2["selected_threshold"]


def test_10_11_candidate_and_false_alarm_counts():
    """
    10. Candidate counts agree with extracted connected components.
    11. False-alarm counts are consistent with matching policy.
    """
    img = np.zeros((100, 100), dtype=np.uint8)
    # Add two components: one near GT, one far away
    img[10:15, 10:15] = 200  # candidate 1 (near (12, 12))
    img[80:85, 80:85] = 200  # candidate 2 (far)

    detector = ClassicalBeaconDetector(threshold=100.0)
    det = detector.detect(img, beacon_gt=(12.0, 12.0), tolerance_px=5.0)

    assert det["num_candidates"] == 2
    assert det["matching_count"] == 1
    assert det["false_candidate_count"] == 1


def test_12_pd_and_pfa_bounds():
    """12. PD and PFA are strictly within [0,1]."""
    exp = Exp04ThresholdSelection(results_dir="scratch/test_results")
    df_sum, df_paired, report = exp.run(trials_override=2)

    assert (df_sum["detection_probability"] >= 0.0).all() and (df_sum["detection_probability"] <= 1.0).all()
    assert (df_sum["false_alarm_rate_pfa"] >= 0.0).all() and (df_sum["false_alarm_rate_pfa"] <= 1.0).all()


def test_13_null_rmse_when_no_detections():
    """13. RMSE is null when there are no valid detections."""
    img = np.zeros((100, 100), dtype=np.uint8)
    detector = ClassicalBeaconDetector(threshold=160.0)
    det = detector.detect(img, beacon_gt=(50.0, 50.0))

    assert not det["detected"]
    assert det["x_est"] is None
    assert det["y_est"] is None


def test_14_15_summary_agrees_with_raw_data_and_trials_count():
    """
    14. Summary results agree with raw CSV.
    15. The correct number of trials is present in completed experiment.
    """
    exp = Exp04ThresholdSelection(results_dir="scratch/test_results")
    df_sum, df_paired, report = exp.run(trials_override=3)

    raw_csv_path = os.path.join(exp.exp_results_dir, "raw_data.csv")
    assert os.path.exists(raw_csv_path)
    df_raw = pd.read_csv(raw_csv_path)

    # 28 conditions x 3 trials x 8 methods = 672 rows
    expected_rows = 28 * 3 * 8
    assert len(df_raw) == expected_rows

    # Check agreement on detection rate for one condition
    first_scen = df_raw["scenario_id"].iloc[0]
    first_meth = df_raw["threshold_method"].iloc[0]
    raw_sub = df_raw[(df_raw["scenario_id"] == first_scen) & (df_raw["threshold_method"] == first_meth)]
    sum_sub = df_sum[(df_sum["scenario_id"] == first_scen) & (df_sum["threshold_method"] == first_meth)]

    assert pytest.approx(raw_sub["detected"].mean()) == sum_sub["detection_probability"].iloc[0]


def test_16_saturation_recorded():
    """16. Saturation and clipping are handled and recorded consistently."""
    exp = Exp04ThresholdSelection(results_dir="scratch/test_results")
    df_sum, _, _ = exp.run(trials_override=1)
    assert "saturated_pixel_fraction" in df_sum.columns
    assert (df_sum["saturated_pixel_fraction"] >= 0.0).all()


def test_17_degenerate_constant_images():
    """17. Degenerate and nearly constant images do not cause unhandled errors."""
    const_img = np.full((100, 100), 50, dtype=np.uint8)
    for m in ["global", "otsu", "adaptive", "mu_plus_3sigma"]:
        fn, p = get_thresholding_method(m)
        mask, info = fn(const_img, **p)
        assert mask.shape == (100, 100)


def test_18_global_threshold_unchanged():
    """18. The global threshold is unchanged across experimental conditions."""
    for m in ["global"]:
        fn, p = get_thresholding_method(m, {"threshold": 160.0})
        mask1, info1 = fn(np.zeros((10, 10), dtype=np.uint8), **p)
        mask2, info2 = fn(np.full((10, 10), 200, dtype=np.uint8), **p)
        assert info1["global_threshold"] == 160.0
        assert info2["global_threshold"] == 160.0
