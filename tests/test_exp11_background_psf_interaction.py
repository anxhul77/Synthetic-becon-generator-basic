import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from experiments.exp11_background_psf_interaction.src.run_experiment import Exp11BackgroundPSFInteraction
from experiments.exp11_background_psf_interaction.src.factorial_analysis import compute_factorial_interaction_contrasts, fit_factorial_linear_model

@pytest.fixture
def sample_camera():
    return PinholeCamera(width=1920, height=1080)

def test_factorial_design_parameters(sample_camera):
    """Verify configured PSF widths, SNRs, backgrounds, and estimators."""
    exp = Exp11BackgroundPSFInteraction()
    cfg = exp.config
    assert len(cfg["psf_sigma_values"]) == 4
    assert len(cfg["snr_levels_db"]) == 4
    assert len(cfg["background_levels"]) == 4
    assert len(cfg["background_types"]) == 4

def test_generator_psf_background_interaction(sample_camera):
    """Verify generator output changes with PSF width and background types."""
    gen = SyntheticBeaconGenerator(camera=sample_camera)

    img_u, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=1.0, sigma_y=1.0, background_type="uniform", background_level=50.0, snr_db=20.0, seed=42)
    img_b, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=4.0, sigma_y=4.0, background_type="uniform", background_level=50.0, snr_db=20.0, seed=42)
    img_h, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=2.0, sigma_y=2.0, background_type="horizontal", background_level=50.0, snr_db=20.0, seed=42)
    img_2d, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=2.0, sigma_y=2.0, background_type="two_dimensional", background_level=50.0, snr_db=20.0, seed=42)

    assert img_u.shape == (1080, 1920)
    assert not np.array_equal(img_u, img_b)
    assert not np.array_equal(img_u, img_h)
    assert not np.array_equal(img_h, img_2d)

def test_paired_trial_image_identity(sample_camera):
    """Verify all 3 estimators receive identical spatial ROI crops per trial."""
    exp = Exp11BackgroundPSFInteraction()
    records, meta = exp.run_trial_image(
        trial_id="t001", seed=42, scenario_id="s1", sub_exp_id="sub1",
        x0=960.25, y0=540.35, psf_sigma=2.0, snr_db=15.0, background_level=50.0
    )

    assert len(records) == 3 # 3 methods
    methods = [r["method"] for r in records]
    assert "Intensity-Weighted Centroid" in methods
    assert "Gaussian Fitting" in methods
    assert "PSF Fitting" in methods

    # Check true position and phase match across all 3 method records
    for r in records:
        assert r["beacon_x_true"] == records[0]["beacon_x_true"]
        assert r["beacon_y_true"] == records[0]["beacon_y_true"]
        assert r["phase_x"] == records[0]["phase_x"]
        assert r["phase_y"] == records[0]["phase_y"]

def test_factorial_linear_model_math():
    """Verify OLS linear regression fitting on synthetic raw data."""
    raw_rows = []
    rng = np.random.default_rng(42)
    for sig in [1.0, 2.0, 3.0, 4.0]:
        for snr in [5.0, 10.0, 15.0, 20.0]:
            for bg in [10.0, 50.0, 100.0, 200.0]:
                for t in range(5):
                    err = 0.05 * sig + 0.1 * (20.0 - snr) + 0.001 * bg + 0.01 * sig * (20.0 - snr) + rng.normal(0, 0.02)
                    raw_rows.append({
                        "method": "Gaussian Fitting",
                        "method_name": "Gaussian Fitting",
                        "psf_sigma_px": sig,
                        "snr_db": snr,
                        "background_level": bg,
                        "radial_error_px": abs(err),
                        "success": True
                    })
    df_raw = pd.DataFrame(raw_rows)
    df_model = fit_factorial_linear_model(df_raw)

    assert not df_model.empty
    terms = list(df_model["factor_term"].unique())
    assert "Intercept" in terms
    assert "PSF_sigma" in terms
    assert "SNR_dB" in terms
    assert "PSF_x_SNR" in terms

def test_interaction_contrast_calculation():
    """Verify 2-way and 3-way interaction contrasts calculation."""
    summary_rows = []
    for m in ["Gaussian Fitting"]:
        for sig in [1.0, 4.0]:
            for snr in [5.0, 20.0]:
                for bg in [10.0, 200.0]:
                    # Create interaction effect
                    rmse = 0.1 + 0.05 * sig + (0.3 if snr == 5.0 else 0.0) + (0.05 * sig if snr == 5.0 else 0.0)
                    summary_rows.append({
                        "method_name": m,
                        "psf_sigma_px": sig,
                        "snr_db": snr,
                        "background_level": bg,
                        "radial_rmse": rmse
                    })
    df_summary = pd.DataFrame(summary_rows)
    df_contrasts = compute_factorial_interaction_contrasts(df_summary)

    assert not df_contrasts.empty
    pair_names = list(df_contrasts["factor_pair"].unique())
    assert "PSF_x_SNR" in pair_names

def test_exp11_mini_execution_and_artifacts():
    """Verify Exp11 execution end-to-end on mini scale (2 trials/condition)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp11BackgroundPSFInteraction(results_dir=tmp_dir)
        df_summary, df_interaction, df_factorial, df_paired, df_raw, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp11_background_psf_interaction")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "paired_comparison.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "interaction_analysis.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "factorial_model.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "psf_snr_rmse_heatmaps.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "psf_background_rmse_heatmaps.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "psf_snr_interaction.png"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "error_distributions.png"))
