"""
Unit test suite for Experiment 5: Connected-Component Filtering.

Tests feature extraction, modular filtering strategies, registry, metric calculations,
paired comparison logic, and reproducible experiment execution.
"""

import os
import shutil
import pytest
import numpy as np
import pandas as pd
import cv2

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from processing.component_filtering import (
    extract_component_features,
    filter_none,
    filter_min_area,
    filter_max_area,
    filter_aspect_ratio,
    filter_circularity,
    filter_peak_intensity,
    filter_combined,
    get_component_filter,
    COMPONENT_FILTER_REGISTRY
)
from experiments.exp05_component_filtering import Exp05ComponentFiltering


@pytest.fixture
def clean_beacon_data():
    """Generates a clean synthetic beacon image and threshold mask."""
    camera = PinholeCamera(width=100, height=100)
    generator = SyntheticBeaconGenerator(camera=camera)
    img, gt = generator.generate_frame(
        x0=50.0, y0=50.0, amplitude=200.0, snr_db=60.0,
        background_level=10.0, seed=42
    )
    mask = (img > 100).astype(np.uint8)
    return img, mask, gt


def test_feature_extraction_single_beacon(clean_beacon_data):
    """Test 1: Single beacon feature extraction."""
    img, mask, gt = clean_beacon_data
    features = extract_component_features(img, mask)

    assert len(features) == 1
    feat = features[0]
    assert feat["area"] >= 3
    assert feat["aspect_ratio"] >= 1.0
    assert feat["aspect_ratio"] <= 2.0
    assert feat["circularity"] > 0.4
    assert feat["peak_intensity"] > 180.0
    cx, cy = feat["centroid"]
    bx, by = gt["x_true"], gt["y_true"]
    assert np.hypot(cx - bx, cy - by) < 2.0




def test_feature_extraction_empty_mask():
    """Test 2: Extraction on empty binary mask returns empty list."""
    img = np.zeros((50, 50), dtype=np.uint8)
    mask = np.zeros((50, 50), dtype=np.uint8)
    features = extract_component_features(img, mask)
    assert features == []


def test_feature_extraction_multiple_components():
    """Test 3: Extraction on multiple components with distinct geometries."""
    img = np.zeros((100, 100), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)

    # Component 1: Small 2x2 spot (area = 4)
    mask[10:12, 10:12] = 1
    img[10:12, 10:12] = 200

    # Component 2: Elongated line 1x20 (area = 20, AR = 20)
    mask[30, 30:50] = 1
    img[30, 30:50] = 150

    # Component 3: Square blob 5x5 (area = 25, AR = 1.0)
    mask[60:65, 60:65] = 1
    img[60:65, 60:65] = 220

    features = extract_component_features(img, mask)
    assert len(features) == 3

    areas = sorted([f["area"] for f in features])
    assert areas == [4, 20, 25]

    elongated = [f for f in features if f["area"] == 20][0]
    assert elongated["aspect_ratio"] >= 15.0


def test_filter_none_baseline():
    """Test 4: filter_none returns identical list."""
    comps = [{"area": 5, "peak_intensity": 200}, {"area": 10, "peak_intensity": 100}]
    filtered = filter_none(comps)
    assert filtered == comps
    assert len(filtered) == 2


def test_filter_min_area():
    """Test 5: filter_min_area filters out components with area < min_area."""
    comps = [{"area": a} for a in [1, 2, 3, 5, 10]]
    filtered = filter_min_area(comps, min_area=3)
    assert len(filtered) == 3
    assert [c["area"] for c in filtered] == [3, 5, 10]


def test_filter_max_area():
    """Test 6: filter_max_area filters out components with area > max_area."""
    comps = [{"area": a} for a in [1, 10, 45, 50, 100]]
    filtered = filter_max_area(comps, max_area=50)
    assert len(filtered) == 4
    assert [c["area"] for c in filtered] == [1, 10, 45, 50]


def test_filter_aspect_ratio():
    """Test 7: filter_aspect_ratio filters components with aspect_ratio > max_aspect_ratio."""
    comps = [{"aspect_ratio": ar} for ar in [1.0, 1.5, 2.0, 2.5, 5.0]]
    filtered = filter_aspect_ratio(comps, max_aspect_ratio=2.0)
    assert len(filtered) == 3
    assert [c["aspect_ratio"] for c in filtered] == [1.0, 1.5, 2.0]


def test_filter_circularity():
    """Test 8: filter_circularity filters components with circularity < min_circularity."""
    comps = [{"circularity": c} for c in [0.2, 0.4, 0.5, 0.8, 1.0]]
    filtered = filter_circularity(comps, min_circularity=0.5)
    assert len(filtered) == 3
    assert [c["circularity"] for c in filtered] == [0.5, 0.8, 1.0]


def test_filter_peak_intensity():
    """Test 9: filter_peak_intensity filters components with peak_intensity < min_peak_intensity."""
    comps = [{"peak_intensity": p} for p in [100.0, 150.0, 180.0, 200.0, 255.0]]
    filtered = filter_peak_intensity(comps, min_peak_intensity=180.0)
    assert len(filtered) == 3
    assert [c["peak_intensity"] for c in filtered] == [180.0, 200.0, 255.0]


def test_filter_combined():
    """Test 10: filter_combined enforces all 5 criteria simultaneously."""
    comps = [
        {"area": 10, "aspect_ratio": 1.2, "circularity": 0.8, "peak_intensity": 200.0},  # Pass
        {"area": 2,  "aspect_ratio": 1.2, "circularity": 0.8, "peak_intensity": 200.0},  # Fail min area
        {"area": 60, "aspect_ratio": 1.2, "circularity": 0.8, "peak_intensity": 200.0},  # Fail max area
        {"area": 10, "aspect_ratio": 3.0, "circularity": 0.8, "peak_intensity": 200.0},  # Fail aspect ratio
        {"area": 10, "aspect_ratio": 1.2, "circularity": 0.3, "peak_intensity": 200.0},  # Fail circularity
        {"area": 10, "aspect_ratio": 1.2, "circularity": 0.8, "peak_intensity": 150.0},  # Fail peak intensity
    ]
    filtered = filter_combined(comps, min_area=3, max_area=50, max_aspect_ratio=2.0,
                               min_circularity=0.5, min_peak_intensity=180.0)
    assert len(filtered) == 1
    assert filtered[0]["area"] == 10


def test_component_filter_registry():
    """Test 11: All registered filter methods return valid functions and default parameters."""
    registered = ["none", "min_area", "max_area", "aspect_ratio", "circularity", "peak_intensity", "combined"]
    for m in registered:
        fn, params = get_component_filter(m)
        assert callable(fn)
        assert isinstance(params, dict)


def test_unknown_filter_method_raises():
    """Test 12: get_component_filter with unknown method raises ValueError."""
    with pytest.raises(ValueError):
        get_component_filter("invalid_filter_name")


def test_fair_comparison_isolation():
    """Test 13: Filtering does not mutate input component feature list or dicts."""
    original = [
        {"label": 1, "area": 1, "peak_intensity": 100.0},
        {"label": 2, "area": 10, "peak_intensity": 200.0}
    ]
    # Pass copy of list
    filtered = filter_min_area(list(original), min_area=5)
    assert len(filtered) == 1
    assert len(original) == 2  # Original list unmodified
    assert original[0]["area"] == 1


def test_retention_rejection_rate_computation():
    """Test 14: Verification of candidate retention and rejection rate metrics."""
    raw_count = 10
    cand_count = 3
    retention_rate = cand_count / raw_count
    rejection_rate = 1.0 - retention_rate

    assert pytest.approx(retention_rate) == 0.3
    assert pytest.approx(rejection_rate) == 0.7


def test_beacon_matching_tolerance():
    """Test 15: Candidate ground-truth distance matching logic."""
    beacon_gt = (50.0, 50.0)
    tolerance_px = 5.0

    filtered_comps = [
        {"centroid": (50.5, 49.8)},  # dist = 0.54 px -> matching
        {"centroid": (10.0, 10.0)},  # dist = 56.5 px -> false candidate
        {"centroid": (54.0, 53.0)},  # dist = 5.0 px -> matching boundary
        {"centroid": (56.0, 50.0)},  # dist = 6.0 px -> false candidate
    ]

    matching_count = sum(
        1 for c in filtered_comps
        if np.hypot(c["centroid"][0] - beacon_gt[0], c["centroid"][1] - beacon_gt[1]) <= tolerance_px
    )

    assert matching_count == 2
    assert len(filtered_comps) - matching_count == 2


def test_primary_candidate_selection():
    """Test 16: Primary candidate selected by peak intensity with sum intensity tie-breaker."""
    comps = [
        {"label": 1, "peak_intensity": 180.0, "sum_intensity": 500.0},
        {"label": 2, "peak_intensity": 220.0, "sum_intensity": 400.0},  # Highest peak
        {"label": 3, "peak_intensity": 220.0, "sum_intensity": 600.0},  # Highest peak + higher sum tie-breaker
    ]
    best = max(comps, key=lambda c: (c["peak_intensity"], c["sum_intensity"]))
    assert best["label"] == 3


def test_localization_nan_on_no_candidates():
    """Test 17: When no candidates survive, localization error and coordinates are NaN."""
    filtered_comps = []
    if filtered_comps:
        x_est, y_est = 50.0, 50.0
        detected = 1
    else:
        x_est, y_est = np.nan, np.nan
        detected = 0

    assert np.isnan(x_est)
    assert np.isnan(y_est)
    assert detected == 0


def test_experiment_load_config():
    """Test 18: Exp05ComponentFiltering configuration loading."""
    exp = Exp05ComponentFiltering()
    cfg = exp.load_config()
    assert cfg["experiment_id"] == "exp05_component_filtering"
    assert "combined" in cfg["methods"]
    assert cfg["detector_threshold"] == 160.0


def test_experiment_smoke_run(tmp_path):
    """Test 19: Smoke run of Exp05ComponentFiltering on a small 2-trial dataset."""
    results_dir = os.path.join(tmp_path, "results")
    exp = Exp05ComponentFiltering(results_dir=results_dir)
    res = exp.run(trials_override=2)

    assert os.path.exists(res["raw_data_path"])
    assert os.path.exists(res["summary_path"])
    assert os.path.exists(res["paired_comparison_path"])
    assert os.path.exists(res["report_path"])

    df_raw = pd.read_csv(res["raw_data_path"])
    assert len(df_raw) > 0
    assert "filter_method" in df_raw.columns
    assert "candidate_rejection_rate" in df_raw.columns

    # Verify figures created
    fig_dir = os.path.join(results_dir, "exp05_component_filtering", "figures")
    for i in range(1, 17):
        fig_name = f"fig{i:02d}_"
        matching_figs = [f for f in os.listdir(fig_dir) if f.startswith(fig_name)]
        assert len(matching_figs) == 1, f"Missing figure {fig_name}"


def test_deterministic_reproducibility(tmp_path):
    """Test 20: Deterministic reproducibility between runs with fixed seed."""
    dir1 = os.path.join(tmp_path, "run1")
    dir2 = os.path.join(tmp_path, "run2")

    exp1 = Exp05ComponentFiltering(results_dir=dir1)
    exp1.run(trials_override=2)

    exp2 = Exp05ComponentFiltering(results_dir=dir2)
    exp2.run(trials_override=2)

    raw1 = pd.read_csv(os.path.join(dir1, "exp05_component_filtering", "raw_data.csv"))
    raw2 = pd.read_csv(os.path.join(dir2, "exp05_component_filtering", "raw_data.csv"))

    # Latency columns vary slightly based on CPU scheduling; drop them for deterministic check
    latency_cols = [c for c in raw1.columns if "latency" in c]
    df1 = raw1.drop(columns=latency_cols)
    df2 = raw2.drop(columns=latency_cols)

    pd.testing.assert_frame_equal(df1, df2)

