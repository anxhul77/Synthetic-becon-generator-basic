"""
Core mathematical functions and calculations for Experiment 18:
Continuous constant-velocity state prediction, continuous process covariance Q(h),
Mahalanobis distance, covariance eigen-decomposition, ellipse geometry, and Wilson score CI.
"""
import numpy as np
from typing import Tuple, Dict, Any

def compute_F_h(h: float) -> np.ndarray:
    """
    Continuous-time constant-velocity state transition matrix F(h) for prediction horizon h [seconds].
    State: [u, v, u_dot, v_dot]^T
    """
    return np.array([
        [1.0, 0.0, float(h), 0.0],
        [0.0, 1.0, 0.0, float(h)],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], dtype=np.float64)

def compute_Q_h(h: float, q_u: float, q_v: float) -> np.ndarray:
    """
    Continuous-time process noise covariance Q(h) for continuous acceleration noise PSD q_u, q_v.
    Q_x(h) = q_u * [[h^3/3, h^2/2], [h^2/2, h]]
    Q_y(h) = q_v * [[h^3/3, h^2/2], [h^2/2, h]]
    """
    h = float(h)
    h2 = h * h
    h3 = h2 * h

    Q = np.zeros((4, 4), dtype=np.float64)
    # x dimension (u)
    Q[0, 0] = q_u * h3 / 3.0
    Q[0, 2] = q_u * h2 / 2.0
    Q[2, 0] = q_u * h2 / 2.0
    Q[2, 2] = q_u * h

    # y dimension (v)
    Q[1, 1] = q_v * h3 / 3.0
    Q[1, 3] = q_v * h2 / 2.0
    Q[3, 1] = q_v * h2 / 2.0
    Q[3, 3] = q_v * h

    return Q

def predict_state_and_cov(
    x_hat_t: np.ndarray,
    P_t: np.ndarray,
    h: float,
    q_u: float,
    q_v: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Predicts state x_hat(t+h|t) and covariance P(t+h|t) for prediction horizon h.
    Returns (x_pred, P_pred, Sigma_h) where Sigma_h is the 2x2 position covariance.
    """
    F_h = compute_F_h(h)
    Q_h = compute_Q_h(h, q_u, q_v)

    x_pred = F_h @ x_hat_t
    P_pred = F_h @ P_t @ F_h.T + Q_h

    # Extract 2x2 position covariance
    Sigma_h = P_pred[0:2, 0:2]

    # Enforce strict symmetry
    Sigma_h = 0.5 * (Sigma_h + Sigma_h.T)

    return x_pred, P_pred, Sigma_h

def compute_mahalanobis_sq(
    error_2d: np.ndarray,
    Sigma_h: np.ndarray
) -> float:
    """
    Computes squared Mahalanobis distance d_h^2 = e_h^T * Sigma_h^{-1} * e_h.
    """
    error_2d = np.asarray(error_2d, dtype=np.float64)
    Sigma_inv = np.linalg.inv(Sigma_h)
    d_sq = float(error_2d.T @ Sigma_inv @ error_2d)
    return max(0.0, d_sq)

def compute_ellipse_geometry(
    Sigma_h: np.ndarray,
    chi2_val: float
) -> Tuple[float, float, float]:
    """
    Computes semi-major axis a, semi-minor axis b, and orientation angle phi (in degrees)
    for uncertainty ellipse at confidence level threshold chi2_val.
    """
    eigvals, eigvecs = np.linalg.eigh(Sigma_h)
    # Sort eigenvalues in descending order
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    l1, l2 = max(1e-12, eigvals[0]), max(1e-12, eigvals[1])

    a = float(np.sqrt(chi2_val * l1))
    b = float(np.sqrt(chi2_val * l2))

    v1 = eigvecs[:, 0]
    phi_rad = float(np.arctan2(v1[1], v1[0]))
    phi_deg = float(np.degrees(phi_rad))

    return a, b, phi_deg

def compute_wilson_ci(
    successes: int,
    total: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Computes Wilson score 95% confidence interval for proportion.
    """
    if total <= 0:
        return 0.0, 0.0
    p_hat = successes / total
    z = 1.959963984540054  # for 95%
    denom = 1.0 + z**2 / total
    centre = (p_hat + z**2 / (2 * total)) / denom
    margin = (z * np.sqrt((p_hat * (1.0 - p_hat) + z**2 / (4 * total)) / total)) / denom

    lower = max(0.0, float(centre - margin))
    upper = min(1.0, float(centre + margin))
    return lower, upper
