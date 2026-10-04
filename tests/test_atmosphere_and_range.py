"""
Unit tests for Traceable Link Model, Atmospheric Propagation Scenarios, and Operating Envelope Evaluation.
"""

import os
import numpy as np
import pytest
import pandas as pd

from generator.atmosphere import AtmosphericModel, kruse_attenuation_alpha, rain_attenuation_alpha
from experiments.exp13_beacon_range.src.optical_power import OpticalLinkRangeModel, OperatingEnvelopeEvaluator
from experiments.exp12_atmospheric_degradation.src.run_experiment import Exp12AtmosphericDegradation
from experiments.exp13_beacon_range.src.run_experiment import Exp13BeaconRange


def test_kruse_attenuation_model():
    # Clear sky (V = 23 km, 1550 nm)
    gamma_clear = kruse_attenuation_alpha(1550.0, 23.0)
    assert 0.01 < gamma_clear < 0.10

    # Haze (V = 5 km, 1550 nm)
    gamma_haze = kruse_attenuation_alpha(1550.0, 5.0)
    assert gamma_haze > gamma_clear

    # Fog (V = 1.5 km, 1550 nm)
    gamma_fog = kruse_attenuation_alpha(1550.0, 1.5)
    assert gamma_fog > gamma_haze


def test_optical_link_model():
    link = OpticalLinkRangeModel(
        wavelength_nm=1550.0,
        transmit_power_mw=500.0,
        beam_waist_m=0.025,
        receiver_aperture_m=0.10,
        detector_noise_floor_dn=3.0
    )

    # Beam waist expands with distance
    w1 = link.calculate_beam_radius(1.0)
    w10 = link.calculate_beam_radius(10.0)
    assert w10 > w1

    # Received amplitude decreases with range and attenuation
    amp_1km = link.calculate_received_amplitude_dn(1.0, attenuation_alpha_km=0.08)
    amp_10km = link.calculate_received_amplitude_dn(10.0, attenuation_alpha_km=0.08)
    assert amp_1km > amp_10km


def test_operating_envelope_compliance():
    evaluator = OperatingEnvelopeEvaluator(
        min_p_detection=0.95,
        max_p_false_alarm=0.01,
        max_angular_rmse_urad=100.0,
        min_signal_amplitude_dn=10.5
    )

    # Compliant case
    res_comp = evaluator.evaluate_compliance(
        p_detection=0.98,
        p_false_alarm=0.005,
        angular_rmse_urad=45.0,
        received_amplitude_dn=120.0
    )
    assert res_comp["is_fully_compliant"]

    # Non-compliant: signal amplitude below sensitivity limit
    res_weak = evaluator.evaluate_compliance(
        p_detection=0.98,
        p_false_alarm=0.005,
        angular_rmse_urad=45.0,
        received_amplitude_dn=5.0  # Below 10.5 DN
    )
    assert not res_weak["is_fully_compliant"]


def test_exp12_run_scenarios():
    exp12 = Exp12AtmosphericDegradation(results_dir="scratch/test_exp12_output")
    df_raw, df_summary, report = exp12.run(trials_override=2)

    assert len(df_raw) > 0
    assert len(df_summary) > 0
    assert "clear" in df_summary["scenario_name"].values
    assert "fog" in df_summary["scenario_name"].values
    assert os.path.exists("scratch/test_exp12_output/exp12_atmospheric_degradation/summary.csv")


def test_exp13_run_link_range():
    exp13 = Exp13BeaconRange(results_dir="scratch/test_exp13_output")
    df_raw, df_summary, report = exp13.run(trials_override=2)

    assert len(df_raw) > 0
    assert len(df_summary) > 0
    assert "is_fully_compliant" in df_summary.columns
    # Check operating statement present without universal 20 km claim
    assert "The tracker satisfies the selected detection" in report
    assert os.path.exists("scratch/test_exp13_output/exp13_beacon_range/summary.csv")
