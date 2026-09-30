import pytest
import numpy as np
import pandas as pd

from experiments.exp23_architecture.sequential_pipeline import SequentialBeaconPipeline
from experiments.exp23_architecture.parallel_pipeline import ParallelBeaconPipeline
from experiments.exp23_architecture.metrics import compute_architecture_summary, compute_paired_comparison_metrics
from experiments.exp23_architecture.benchmark import Exp23ArchitectureBenchmark

@pytest.fixture
def sample_frame():
    img = np.zeros((1080, 1920), dtype=np.uint8)
    # Place bright spot at (960, 540)
    y_grid, x_grid = np.ogrid[:1080, :1920]
    spot = 200.0 * np.exp(-((x_grid - 960)**2 + (y_grid - 540)**2) / 8.0)
    img = np.clip(spot, 0, 255).astype(np.uint8)
    return img

def test_sequential_pipeline_execution(sample_frame):
    seq_pipe = SequentialBeaconPipeline()
    res = seq_pipe.process_frame(sample_frame, frame_id="test_seq_001", beacon_gt=(960.0, 540.0))

    assert res["architecture"] == "sequential"
    assert res["end_to_end_latency_ms"] > 0.0
    assert res["classical_latency_ms"] >= 0.0
    assert res["ai_latency_ms"] >= 0.0
    assert "detected" in res
    assert res["detected"] == True

def test_parallel_pipeline_execution(sample_frame):
    par_pipe = ParallelBeaconPipeline()
    res = par_pipe.process_frame(sample_frame, frame_id="test_par_001", beacon_gt=(960.0, 540.0))
    par_pipe.shutdown()

    assert res["architecture"] == "parallel"
    assert res["end_to_end_latency_ms"] > 0.0
    assert res["dispatch_latency_ms"] >= 0.0
    assert res["synchronization_latency_ms"] >= 0.0
    assert "detected" in res
    assert res["detected"] == True

def test_functional_equivalence(sample_frame):
    seq_pipe = SequentialBeaconPipeline()
    par_pipe = ParallelBeaconPipeline()

    res_seq = seq_pipe.process_frame(sample_frame, frame_id="eq_001", beacon_gt=(960.0, 540.0))
    res_par = par_pipe.process_frame(sample_frame, frame_id="eq_001", beacon_gt=(960.0, 540.0))
    par_pipe.shutdown()

    assert res_seq["detected"] == res_par["detected"]
    assert res_seq["fusion_status"] == res_par["fusion_status"]
    if res_seq["detected"]:
        assert np.isclose(res_seq["x_est"], res_par["x_est"], atol=1e-3)
        assert np.isclose(res_seq["y_est"], res_par["y_est"], atol=1e-3)

def test_benchmark_metrics_formulas():
    records_seq = [
        {"frame_id": "f1", "architecture": "sequential", "end_to_end_latency_ms": 10.0, "detected": 1, "x_est": 100.0, "y_est": 100.0, "x_true": 100.0, "y_true": 100.0},
        {"frame_id": "f2", "architecture": "sequential", "end_to_end_latency_ms": 10.0, "detected": 1, "x_est": 200.0, "y_est": 200.0, "x_true": 200.0, "y_true": 200.0}
    ]
    records_par = [
        {"frame_id": "f1", "architecture": "parallel", "end_to_end_latency_ms": 5.0, "detected": 1, "x_est": 100.0, "y_est": 100.0, "x_true": 100.0, "y_true": 100.0},
        {"frame_id": "f2", "architecture": "parallel", "end_to_end_latency_ms": 5.0, "detected": 1, "x_est": 200.0, "y_est": 200.0, "x_true": 200.0, "y_true": 200.0}
    ]
    df_seq = pd.DataFrame(records_seq)
    df_par = pd.DataFrame(records_par)

    sum_seq = compute_architecture_summary(df_seq, "sequential")
    sum_par = compute_architecture_summary(df_par, "parallel")
    merged, paired_sum = compute_paired_comparison_metrics(df_seq, df_par)

    assert sum_seq["mean_latency_ms"] == 10.0
    assert sum_par["mean_latency_ms"] == 5.0
    assert paired_sum["mean_speedup"] == 2.0
    assert paired_sum["mean_paired_difference_ms"] == 5.0

def test_benchmark_runner_pilot():
    exp = Exp23ArchitectureBenchmark()
    df_raw, df_summary, report_md = exp.run(trials_override=5)

    assert len(df_raw) == 10  # 5 seq + 5 par
    assert len(df_summary) == 2
    assert "EXPERIMENT 23" in report_md
