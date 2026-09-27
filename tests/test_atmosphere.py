import numpy as np
import pytest
from generator.atmosphere import AtmosphericModel

def test_transmittance_analytical():
    alpha = 0.0002
    L = 5.0
    atmo = AtmosphericModel(attenuation_alpha=alpha, range_km=L, condition="clear")
    expected_T = np.exp(-alpha * L)
    assert pytest.approx(atmo.calculate_transmittance(), abs=1e-10) == expected_T

def test_received_amplitude():
    alpha = 0.0001
    L = 10.0
    A0 = 200.0
    atmo = AtmosphericModel(attenuation_alpha=alpha, range_km=L)
    expected_A_recv = A0 * np.exp(-alpha * L)
    assert pytest.approx(atmo.apply_atmosphere(A0), abs=1e-10) == expected_A_recv

def test_limiting_behavior_zero_range():
    atmo = AtmosphericModel(attenuation_alpha=0.005, range_km=0.0)
    assert pytest.approx(atmo.calculate_transmittance(), abs=1e-10) == 1.0
    assert pytest.approx(atmo.apply_atmosphere(150.0), abs=1e-10) == 150.0

def test_transmittance_monotonicity_range():
    atmo1 = AtmosphericModel(attenuation_alpha=0.0001, range_km=2.0)
    atmo2 = AtmosphericModel(attenuation_alpha=0.0001, range_km=10.0)
    assert atmo1.calculate_transmittance() > atmo2.calculate_transmittance()

def test_transmittance_monotonicity_alpha():
    atmo1 = AtmosphericModel(attenuation_alpha=0.0001, range_km=5.0)
    atmo2 = AtmosphericModel(attenuation_alpha=0.001, range_km=5.0)
    assert atmo1.calculate_transmittance() > atmo2.calculate_transmittance()

def test_condition_metadata_only():
    atmo_clear = AtmosphericModel(attenuation_alpha=0.0001, range_km=5.0, condition="clear")
    atmo_fog = AtmosphericModel(attenuation_alpha=0.0001, range_km=5.0, condition="fog")
    assert atmo_clear.condition == "clear"
    assert atmo_fog.condition == "fog"
    # Physics depends solely on alpha and range_km
    assert atmo_clear.calculate_transmittance() == atmo_fog.calculate_transmittance()
