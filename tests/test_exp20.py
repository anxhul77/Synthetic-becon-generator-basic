import pytest
import numpy as np
from experiments.exp20_prediction_error_adaptation.src.innovation_adaptation import (
    compute_innovation_nis,
    compute_error_adapted_amplitude
)

def test_innovation_nis_computation():
    z = np.array([102.0, 501.0])
    x_pred = np.array([100.0, 500.0, 5.0, 0.0])
    H = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]])
    P_pred = np.eye(4) * 0.5
    R = np.eye(2) * 0.1

    nu, S, nis = compute_innovation_nis(z, x_pred, P_pred, H, R)

    np.testing.assert_allclose(nu, np.array([2.0, 1.0]))
    np.testing.assert_allclose(S, np.eye(2) * 0.6)
    # (4/0.6) + (1/0.6) = 5 / 0.6 = 8.3333
    np.testing.assert_allclose(nis, 8.333333333333334, rtol=1e-5)

def test_error_adapted_amplitude():
    sigma_val = 10.0
    gamma = 2.4477
    nis_stat = 9.0  # sqrt(9) = 3.0
    lambda_adapt = 15.0
    A_max = 300.0

    A = compute_error_adapted_amplitude(sigma_val, gamma, nis_stat, lambda_adapt, A_max)

    # 2.4477 * 10 + 15 * 3 = 24.477 + 45 = 69.477
    np.testing.assert_allclose(A, 69.477, rtol=1e-4)

    # Test saturation at A_max
    A_sat = compute_error_adapted_amplitude(100.0, gamma, 100.0, 50.0, A_max)
    assert A_sat == A_max
