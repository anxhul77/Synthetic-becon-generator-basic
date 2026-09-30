import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from experiments.exp12_atmospheric_degradation.src.atmospheric_models import ExtendedAtmosphericModel
from experiments.exp12_atmospheric_degradation.src.detector import FullFrameBeaconDetector
from experiments.exp12_atmospheric_degradation.src.run_experiment import Exp12AtmosphericDegradation

def test_beer_lambert_attenuation_math():
    """Verify Beer-Lambert transmission T(L) = exp(-alpha * L)."""
    atmo = ExtendedAtmosphericModel(attenuation_alpha=0.0001, range_km=10.0)
    t = atmo.calculate_transmittance()
    expected_t = np.exp(-0.0001 * 10.0)
    assert np.isclose(t, expected_t)

    amp_received = atmo.apply_attenuation(150.0)
    assert np.isclose(amp_received, 150.0 * expected_t)

def test_turbulence_scintillation_and_wander():
    """Verify turbulence beam wander and scintillation models."""
    rng = np.random.default_rng(42)
    atmo = ExtendedAtmosphericModel(range_km=5.0, turbulence_strength=0.5)

    x0, y0 = 960.0, 540.0
    x_t, y_t, amp_t, sig_t = atmo.apply_turbulence(x0, y0, amplitude=150.0, sigma_0=2.0, rng=rng)

    assert x_t != x0 or y_t != y0  # Wander occurred
    assert sig_t > 2.0  # Spot broadening occurred

def test_scattering_halo_energy_conservation():
    """Verify scattering halo redistributes energy without losing total integrated power."""
    atmo = ExtendedAtmosphericModel(scattering_fraction=0.2, halo_sigma=10.0)
    img = np.zeros((100, 100), dtype=np.float64)
    img[45:55, 45:55] = 100.0

    scat = atmo.apply_scattering_halo(img, x0=50.0, y0=50.0, total_energy=np.sum(img))
    assert np.isclose(np.sum(img), np.sum(scat), rtol=1e-3)

def test_full_frame_detector():
    """Verify full-frame beacon detector on a synthetic frame."""
    detector = FullFrameBeaconDetector(threshold_multiplier=3.0)
    img = np.zeros((500, 500), dtype=np.uint8)
    img[245:255, 245:255] = 200

    res = detector.detect(img, x_gt=250.0, y_gt=250.0, beacon_present=True)
    assert res["is_detected"] == True
    assert res["num_candidates"] >= 1

def test_exp12_mini_execution():
    """Verify Exp12 end-to-end execution on mini scale."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp12AtmosphericDegradation(results_dir=tmp_dir)
        df_raw, df_summary, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp12_atmospheric_degradation")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "detection_prob_vs_distance.png"))
