import pytest
import numpy as np

from experiments.exp17_prediction_horizon_characterization.src.horizon_analyzer import (
    compute_F_h,
    compute_Q_h,
    predict_state_and_cov,
    validate_covariance_properties,
    compute_angular_error_rad
)
from experiments.exp17_prediction_horizon_characterization.src.run_experiment import Exp17PredictionHorizonCharacterization


def test_dimensional_consistency():
    for h in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        F_h = compute_F_h(h)
        Q_h = compute_Q_h(h, 0.5, 0.5)

        assert F_h.shape == (4, 4)
        assert Q_h.shape == (4, 4)

        x_hat = np.array([100.0, 200.0, 10.0, 5.0], dtype=np.float64)
        P = np.eye(4, dtype=np.float64) * 0.1

        x_pred, P_pred, Sigma_h = predict_state_and_cov(x_hat, P, h)

        assert x_pred.shape == (4,)
        assert P_pred.shape == (4, 4)
        assert Sigma_h.shape == (2, 2)


def test_numerical_stability():
    x_hat = np.array([500.0, 500.0, -15.0, 25.0], dtype=np.float64)
    P = np.eye(4, dtype=np.float64) * 0.5

    for h in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        x_pred, P_pred, Sigma_h = predict_state_and_cov(x_hat, P, h)

        assert np.all(np.isfinite(x_pred))
        assert np.all(np.isfinite(P_pred))
        assert np.all(np.isfinite(Sigma_h))


def test_covariance_symmetry():
    P = np.array([
        [1.0, 0.2, 0.1, 0.05],
        [0.2, 2.0, 0.05, 0.3],
        [0.1, 0.05, 0.5, 0.01],
        [0.05, 0.3, 0.01, 0.8]
    ], dtype=np.float64)
    x_hat = np.zeros(4)

    for h in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        _, P_pred, Sigma_h = predict_state_and_cov(x_hat, P, h)
        val_props = validate_covariance_properties(P_pred)

        assert val_props["is_symmetric"]
        assert np.allclose(P_pred, P_pred.T, atol=1e-8)
        assert np.allclose(Sigma_h, Sigma_h.T, atol=1e-8)


def test_covariance_positive_semidefiniteness():
    P = np.eye(4, dtype=np.float64) * 0.25
    x_hat = np.zeros(4)

    for h in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        _, P_pred, Sigma_h = predict_state_and_cov(x_hat, P, h)
        val_props = validate_covariance_properties(P_pred)

        assert val_props["is_psd"]
        eigvals = np.linalg.eigvalsh(P_pred)
        assert np.all(eigvals >= -1e-10)


def test_correct_horizon_handling():
    exp = Exp17PredictionHorizonCharacterization()
    assert exp.horizons == [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]


def test_reproducibility():
    exp1 = Exp17PredictionHorizonCharacterization()
    df_raw1, df_sum1, _ = exp1.run(trials_override=2)

    exp2 = Exp17PredictionHorizonCharacterization()
    df_raw2, df_sum2, _ = exp2.run(trials_override=2)

    assert np.allclose(df_sum1["position_rmse_px"].values, df_sum2["position_rmse_px"].values)
    assert np.allclose(df_sum1["pred_sigma_u_px"].values, df_sum2["pred_sigma_u_px"].values)


def test_independent_validation_trajectories():
    exp = Exp17PredictionHorizonCharacterization()
    df_raw, df_sum, _ = exp.run(trials_override=2)

    motion_types = set(df_raw["motion_type"])
    assert "linear_cv" in motion_types
    assert "maneuvering_circular" in motion_types
    assert "random_walk_accel" in motion_types
    assert len(df_raw) > 0
    assert len(df_sum) == 6
