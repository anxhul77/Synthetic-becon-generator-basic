import pytest
import numpy as np
from experiments.exp18_uncertainty_ellipse_coverage.src.ellipse_coverage import (
    compute_F_h,
    compute_Q_h,
    predict_state_and_cov,
    compute_mahalanobis_sq,
    compute_ellipse_geometry,
    compute_wilson_ci
)

def test_covariance_symmetry_and_posdef():
    q_u = 0.5
    q_v = 0.5
    for h in [0.5, 1.0, 2.0, 5.0]:
        F = compute_F_h(h)
        Q = compute_Q_h(h, q_u, q_v)

        # Check symmetry
        np.testing.assert_allclose(Q, Q.T, rtol=1e-10, atol=1e-12)

        # Check positive semi-definiteness / eigenvalues
        eigvals = np.linalg.eigvalsh(Q)
        assert np.all(eigvals >= -1e-12)

        P0 = np.eye(4) * 0.1
        P_pred = F @ P0 @ F.T + Q
        np.testing.assert_allclose(P_pred, P_pred.T, rtol=1e-10, atol=1e-12)
        assert np.all(np.linalg.eigvalsh(P_pred) > 0)

def test_prediction_horizon_scaling():
    h1 = 1.0
    h5 = 5.0
    F1 = compute_F_h(h1)
    F5 = compute_F_h(h5)

    x0 = np.array([100.0, 200.0, 10.0, -5.0])
    x1 = F1 @ x0
    x5 = F5 @ x0

    assert x1[0] == 100.0 + 10.0 * 1.0
    assert x5[0] == 100.0 + 10.0 * 5.0
    assert x1[1] == 200.0 - 5.0 * 1.0
    assert x5[1] == 200.0 - 5.0 * 5.0

def test_mahalanobis_distance():
    # Symmetric 2D covariance
    Sigma = np.array([[4.0, 0.0], [0.0, 9.0]])
    e = np.array([2.0, 3.0])  # Exactly 1 sigma along each axis
    d_sq = compute_mahalanobis_sq(e, Sigma)
    # (2^2)/4 + (3^2)/9 = 1 + 1 = 2.0
    np.testing.assert_allclose(d_sq, 2.0, rtol=1e-7)

def test_ellipse_geometry():
    Sigma = np.array([[4.0, 0.0], [0.0, 1.0]])
    chi2_val = 5.991465  # 95%
    a, b, phi_deg = compute_ellipse_geometry(Sigma, chi2_val)
    np.testing.assert_allclose(a, np.sqrt(5.991465 * 4.0), rtol=1e-5)
    np.testing.assert_allclose(b, np.sqrt(5.991465 * 1.0), rtol=1e-5)

def test_wilson_ci():
    low, high = compute_wilson_ci(95, 100, confidence=0.95)
    assert 0.88 < low < 0.93
    assert 0.96 < high < 0.99
