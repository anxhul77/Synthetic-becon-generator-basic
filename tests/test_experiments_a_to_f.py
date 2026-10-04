import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from experiments.exp24_sih_compliance import Exp24SIHCompliance
from experiments.exp25_closed_loop_benchmark import Exp25ClosedLoopBenchmark
from experiments.exp26_mp4_benchmark import Exp26MP4Benchmark
from experiments.exp27_fair_algorithm_ablation import Exp27FairAlgorithmAblation
from experiments.exp28_calibration_uncertainty import Exp28CalibrationUncertainty
from experiments.exp29_realtime_profiling import Exp29RealtimeProfiling


def test_experiment_a_sih_compliance():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp24SIHCompliance(results_dir=tmp_dir)
        df_matrix, report = exp.run(trials_override=2)
        assert os.path.exists(os.path.join(tmp_dir, "exp24_sih_compliance", "sih_requirements_matrix.csv"))
        assert len(df_matrix) == 10
        # Verify throughput >= 20 FPS and status
        fps_row = df_matrix[df_matrix["Requirement"] == ">=20 FPS Processing"].iloc[0]
        assert fps_row["Status"] == "PASS"


def test_experiment_b_closed_loop_benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp25ClosedLoopBenchmark(results_dir=tmp_dir)
        df_bench, report = exp.run(trials_override=2)
        assert os.path.exists(os.path.join(tmp_dir, "exp25_closed_loop_benchmark", "closed_loop_benchmark_summary.csv"))
        assert len(df_bench) >= 11


def test_experiment_c_mp4_benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp26MP4Benchmark(results_dir=tmp_dir)
        df_summary, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp26_mp4_benchmark", "video_benchmark_summary.csv"))
        assert os.path.exists(os.path.join(tmp_dir, "exp26_mp4_benchmark", "video_benchmark_estimates.csv"))


def test_experiment_d_fair_ablation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp27FairAlgorithmAblation(results_dir=tmp_dir)
        df_ablation, report = exp.run(trials_override=2)
        assert os.path.exists(os.path.join(tmp_dir, "exp27_fair_algorithm_ablation", "algorithm_ablation_summary.csv"))
        assert len(df_ablation) == 6


def test_experiment_e_calibration_uncertainty():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp28CalibrationUncertainty(results_dir=tmp_dir)
        df_calib, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp28_calibration_uncertainty", "uncertainty_calibration_summary.csv"))
        assert len(df_calib) >= 6


def test_experiment_f_realtime_profiling():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp29RealtimeProfiling(results_dir=tmp_dir)
        df_prof, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp29_realtime_profiling", "realtime_stage_profiling_summary.csv"))
        assert len(df_prof) == 6
