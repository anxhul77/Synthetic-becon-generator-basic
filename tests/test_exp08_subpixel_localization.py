import os
import numpy as np
import pytest
import pandas as pd

from generator.generator import SyntheticBeaconGenerator
from experiments.exp08_subpixel_localization.src.phase_grid import generate_controlled_phase_grid, assign_phase_bin
from experiments.exp08_subpixel_localization.src.phase_analysis import compute_phase_grid_analysis
from experiments.exp08_subpixel_localization.src.run_experiment import Exp08SubpixelLocalization


def test_generator_fractional_rendering_and_metadata():
    gen = SyntheticBeaconGenerator()
    x0, y0 = 960.375, 540.625
    img, gt = gen.generate_frame(x0=x0, y0=y0, seed=123)

    assert gt["x_true"] == x0
    assert gt["y_true"] == y0
    assert pytest.approx(gt["phi_x"], abs=1e-5) == 0.375
    assert pytest.approx(gt["phi_y"], abs=1e-5) == 0.625

    # Check that PSF peak shifts subpixel
    # Shift x0 by 0.5 px right -> pixel at 961 should get higher intensity than when centered at 960.0
    img_int, _ = gen.generate_frame(x0=960.0, y0=540.0, seed=123)
    img_frac, _ = gen.generate_frame(x0=960.5, y0=540.0, seed=123)

    assert img_frac[540, 961] > img_int[540, 961]


def test_phase_grid_generation_and_binning():
    grid = generate_controlled_phase_grid()
    assert len(grid) == 64
    assert (0.0, 0.0) in grid
    assert (0.875, 0.875) in grid

    assert assign_phase_bin(0.124, 8) == 0.125
    assert assign_phase_bin(0.251, 8) == 0.25


def test_exp08_integration_and_output_generation():
    exp = Exp08SubpixelLocalization(results_dir="scratch/test_exp08_results")
    df_summary, df_phase, df_paired, df_raw, report = exp.run(trials_override=2)

    assert len(df_raw) > 0
    assert len(df_summary) > 0
    assert len(df_phase) > 0
    assert len(df_paired) > 0

    exp_dir = os.path.join(exp.results_dir, exp.experiment_id)
    assert os.path.exists(os.path.join(exp_dir, "raw_data.csv"))
    assert os.path.exists(os.path.join(exp_dir, "summary.csv"))
    assert os.path.exists(os.path.join(exp_dir, "phase_analysis.csv"))
    assert os.path.exists(os.path.join(exp_dir, "paired_comparison.csv"))
    assert os.path.exists(os.path.join(exp_dir, "localization_failures.csv"))
    assert os.path.exists(os.path.join(exp_dir, "report.md"))

    # Verify all 5 methods present in raw dataset
    methods = set(df_raw["method_name"].unique())
    expected_methods = {
        "Bounding Box Center",
        "Binary Centroid",
        "Intensity-Weighted Centroid",
        "Gaussian Fitting",
        "PSF Fitting (Known PSF)"
    }
    assert expected_methods.issubset(methods)
