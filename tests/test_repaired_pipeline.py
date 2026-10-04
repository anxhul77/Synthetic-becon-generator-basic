import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from experiments.exp_psf_repaired.run_experiment import RepairedPSFBenchmark
from experiments.exp_closed_loop_repaired.run_experiment import RepairedClosedLoopBenchmark
from experiments.exp_ablation_repaired.run_experiment import RepairedFairAlgorithmAblation
from experiments.exp_uncertainty_repaired.run_experiment import RepairedUncertaintyCalibration
from experiments.exp_realtime_repaired.run_experiment import RepairedRealtimeProfiling
from experiments.exp_architecture_repaired.run_experiment import RepairedArchitectureBenchmark
from experiments.exp_monte_carlo_repaired.run_experiment import RepairedMonteCarloValidation


def test_repaired_psf_benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedPSFBenchmark(results_dir=tmp_dir)
        df_offset, df_modes, report = exp.run(trials_override=2)
        assert os.path.exists(os.path.join(tmp_dir, "exp_psf", "roi_offset_sweep_decomposed.csv"))
        assert os.path.exists(os.path.join(tmp_dir, "exp_psf", "oracle_vs_blind_summary.csv"))
        assert len(df_offset) == 7
        assert len(df_modes) == 2


def test_repaired_closed_loop_benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedClosedLoopBenchmark(results_dir=tmp_dir)
        df_summary, raw_dfs, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp_closed_loop", "closed_loop_benchmark_summary.csv"))
        assert len(df_summary) == 11


def test_repaired_fair_algorithm_ablation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedFairAlgorithmAblation(results_dir=tmp_dir)
        df_ablation, report = exp.run(trials_override=2)
        assert os.path.exists(os.path.join(tmp_dir, "exp_ablation", "algorithm_ablation_summary.csv"))
        assert len(df_ablation) == 6


def test_repaired_uncertainty_calibration():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedUncertaintyCalibration(results_dir=tmp_dir)
        df_calib, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp_uncertainty", "uncertainty_calibration_summary.csv"))
        assert len(df_calib) == 5


def test_repaired_realtime_profiling():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedRealtimeProfiling(results_dir=tmp_dir)
        df_prof, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp_realtime", "realtime_stage_profiling_summary.csv"))
        assert len(df_prof) == 6


def test_repaired_architecture_benchmark():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedArchitectureBenchmark(results_dir=tmp_dir)
        df_arch, report = exp.run(trials_override=1)
        assert os.path.exists(os.path.join(tmp_dir, "exp_architecture", "architecture_benchmark_summary.csv"))
        assert len(df_arch) == 2


def test_repaired_monte_carlo_validation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = RepairedMonteCarloValidation(results_dir=tmp_dir)
        df_mc, report = exp.run(trials_override=5)
        assert os.path.exists(os.path.join(tmp_dir, "exp_monte_carlo", "monte_carlo_statistical_summary.csv"))
        assert len(df_mc) == 1
