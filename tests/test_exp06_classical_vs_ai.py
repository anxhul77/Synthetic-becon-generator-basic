import os
import shutil
import tempfile
import numpy as np
import pandas as pd
import pytest
import torch

from experiments.exp06_classical_vs_ai.dataset_generator import Exp06DatasetGenerator
from experiments.exp06_classical_vs_ai.ai_detector import BeaconHeatmapNet, AIBeaconDetector
from experiments.exp06_classical_vs_ai.hybrid_detector import HybridBeaconDetector
from experiments.exp06_classical_vs_ai.evaluation import evaluate_predictions, compute_wilson_ci, compute_paired_bootstrap_ci

@pytest.fixture
def temp_dataset_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_dataset_split_disjoint(temp_dataset_dir):
    gen = Exp06DatasetGenerator(base_dir=temp_dataset_dir)
    df_manifest, _ = gen.generate_dataset(num_train=20, num_val=5, num_test=5, save_on_disk=True)

    train_ids = set(df_manifest[df_manifest["split"] == "train"]["image_id"])
    val_ids = set(df_manifest[df_manifest["split"] == "val"]["image_id"])
    test_ids = set(df_manifest[df_manifest["split"] == "test"]["image_id"])

    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0

def test_dataset_disjoint_seeds(temp_dataset_dir):
    gen = Exp06DatasetGenerator(base_dir=temp_dataset_dir)
    df_manifest, _ = gen.generate_dataset(num_train=10, num_val=5, num_test=5, save_on_disk=False)

    train_seeds = set(df_manifest[df_manifest["split"] == "train"]["seed"])
    val_seeds = set(df_manifest[df_manifest["split"] == "val"]["seed"])
    test_seeds = set(df_manifest[df_manifest["split"] == "test"]["seed"])

    assert len(train_seeds.intersection(val_seeds)) == 0
    assert len(train_seeds.intersection(test_seeds)) == 0
    assert len(val_seeds.intersection(test_seeds)) == 0

def test_beacon_free_ground_truth(temp_dataset_dir):
    gen = Exp06DatasetGenerator(base_dir=temp_dataset_dir)
    df_manifest, _ = gen.generate_dataset(num_train=10, num_val=5, num_test=5, save_on_disk=False)

    absent_df = df_manifest[df_manifest["beacon_present"] == False]
    for _, row in absent_df.iterrows():
        assert np.isnan(row["x_true"]) or row["x_true"] is None

def test_ai_detector_inference():
    ai_det = AIBeaconDetector(confidence_threshold=0.5)
    img = np.zeros((1080, 1920), dtype=np.uint8)
    
    # Place a synthetic bright spot at (960, 540)
    y_grid, x_grid = np.ogrid[:1080, :1920]
    spot = 200.0 * np.exp(-((x_grid - 960)**2 + (y_grid - 540)**2) / 8.0)
    img = np.clip(spot, 0, 255).astype(np.uint8)

    res = ai_det.detect(img)
    assert "detected" in res
    assert "inference_latency_ms" in res
    assert res["inference_latency_ms"] >= 0.0

def test_ai_detector_empty_image():
    ai_det = AIBeaconDetector(confidence_threshold=0.5)
    img = np.zeros((1080, 1920), dtype=np.uint8)
    res = ai_det.detect(img)
    
    assert res["detected"] == False
    assert res["x_est"] is None
    assert res["num_candidates"] == 0

def test_hybrid_fusion_deterministic():
    hybrid_det = HybridBeaconDetector(matching_radius_px=5.0, weight_classical=0.5)
    img = np.zeros((1080, 1920), dtype=np.uint8)

    res1 = hybrid_det.detect(img)
    res2 = hybrid_det.detect(img)

    assert res1["detected"] == res2["detected"]
    assert res1["fusion_status"] == res2["fusion_status"]

def test_hybrid_fusion_image_bounds():
    hybrid_det = HybridBeaconDetector(matching_radius_px=5.0)
    img = np.random.randint(0, 50, (1080, 1920), dtype=np.uint8)
    res = hybrid_det.detect(img)

    if res["detected"]:
        assert 0.0 <= res["x_est"] <= 1920.0
        assert 0.0 <= res["y_est"] <= 1080.0

def test_wilson_ci_computation():
    low, high = compute_wilson_ci(0.8, 100)
    assert 0.0 <= low <= 0.8 <= high <= 1.0

def test_paired_bootstrap_ci():
    vec_a = np.array([1.0, 1.0, 1.0, 0.0, 1.0])
    vec_b = np.array([0.0, 1.0, 0.0, 0.0, 0.0])
    mean_diff, low, high = compute_paired_bootstrap_ci(vec_a, vec_b, num_bootstraps=100)

    assert mean_diff > 0
    assert low <= mean_diff <= high

def test_evaluate_predictions_zero_denominators():
    records = [
        {
            "image_id": "img1", "scenario_id": "s1", "detector": "classical",
            "beacon_present": False, "x_true": np.nan, "y_true": np.nan,
            "detected": False, "x_est": np.nan, "y_est": np.nan,
            "false_candidate_count": 0, "localization_error_px": np.nan,
            "total_latency_ms": 5.0
        }
    ]
    df_pred = pd.DataFrame(records)
    df_sum, df_paired = evaluate_predictions(df_pred)

    assert len(df_sum) == 1
    assert df_sum.iloc[0]["pd"] == 0.0
    assert df_sum.iloc[0]["pfa"] == 0.0
