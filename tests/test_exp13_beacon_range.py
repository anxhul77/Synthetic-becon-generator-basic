import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from experiments.exp13_beacon_range.src.optical_power import OpticalLinkRangeModel, OperatingEnvelopeEvaluator
from experiments.exp13_beacon_range.src.run_experiment import Exp13BeaconRange

def test_optical_link_beam_spreading_math():
    """Verify Gaussian beam expansion w(L) and captured optical power calculations."""
    model = OpticalLinkRangeModel(wavelength_nm=1550.0, beam_waist_m=0.05, receiver_aperture_m=0.10)

    # Beam radius at 1 km
    w_1km = model.calculate_beam_radius(1.0)
    assert w_1km > 0.05

    # Power ratio decreases with range
    p_1km = model.calculate_captured_power_ratio(1.0)
    p_10km = model.calculate_captured_power_ratio(10.0)
    assert p_1km > p_10km

def test_operating_envelope_compliance():
    """Verify envelope compliance rules (P_D >= 0.95, P_FA <= 0.01, RMSE <= 100 urad)."""
    evaluator = OperatingEnvelopeEvaluator(min_p_detection=0.95, max_p_false_alarm=0.01, max_angular_rmse_urad=100.0)

    res_good = evaluator.evaluate_compliance(p_detection=0.98, p_false_alarm=0.005, angular_rmse_urad=50.0)
    assert res_good["is_fully_compliant"] == True

    res_bad = evaluator.evaluate_compliance(p_detection=0.90, p_false_alarm=0.005, angular_rmse_urad=50.0)
    assert res_bad["is_fully_compliant"] == False

def test_exp13_mini_execution():
    """Verify Exp13 end-to-end execution on mini scale."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        exp = Exp13BeaconRange(results_dir=tmp_dir)
        df_raw, df_summary, report_md = exp.run(trials_override=2)

        exp_res_dir = os.path.join(tmp_dir, "exp13_beacon_range")
        assert os.path.exists(os.path.join(exp_res_dir, "raw_data.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "summary.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "operating_envelope.csv"))
        assert os.path.exists(os.path.join(exp_res_dir, "report.md"))
        assert os.path.exists(os.path.join(exp_res_dir, "figures", "optical_power_vs_distance.png"))
