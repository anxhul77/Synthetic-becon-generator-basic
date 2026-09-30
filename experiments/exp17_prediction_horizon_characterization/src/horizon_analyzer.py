import numpy as np
from typing import Tuple, Dict, Any

def compute_F_h(h: float) -> np.ndarray:
    """
    Computes continuous-time State Transition Matrix F(h) for prediction horizon h:
    [ 1  0  h  0 ]
    [ 0  1  0  h ]
    [ 0  0  1  0 ]
    [ 0  0  0  1 ]
    """
    h_val = float(h)
    return np.array([
        [1.0, 0.0, h_val, 0.0],
        [0.0, 1.0, 0.0, h_val],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], dtype=np.float64)

def compute_Q_h(h: float, q_u: float = 0.5, q_v: float = 0.5) -> np.ndarray:
    """
    Computes continuous process noise covariance matrix Q(h) for prediction horizon h:
    Q(h) = [ q_u * h^3 / 3,       0,         q_u * h^2 / 2,       0       ]
           [      0,        q_v * h^3 / 3,        0,        q_v * h^2 / 2 ]
           [ q_u * h^2 / 2,       0,           q_u * h,           0       ]
           [      0,        q_v * h^2 / 2,        0,           q_v * h    ]
    """
    h_val = float(h)
    qu = float(q_u)
    qv = float(q_v)

    h2_2 = (h_val ** 2) / 2.0
    h3_3 = (h_val ** 3) / 3.0

    return np.array([
        [qu * h3_3, 0.0, qu * h2_2, 0.0],
        [0.0, qv * h3_3, 0.0, qv * h2_2],
        [qu * h2_2, 0.0, qu * h_val, 0.0],
        [0.0, qv * h2_2, 0.0, qv * h_val]
    ], dtype=np.float64)

def predict_state_and_cov(x_hat: np.ndarray,
                          P: np.ndarray,
                          h: float,
                          q_u: float = 0.5,
                          q_v: float = 0.5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Predicts state x(t+h|t) and covariance P(t+h|t) to horizon h:
    x_pred = F(h) @ x_hat
    P_pred = F(h) @ P @ F(h)^T + Q(h)
    Sigma_h = P_pred[0:2, 0:2]
    """
    F_h = compute_F_h(h)
    Q_h = compute_Q_h(h, q_u, q_v)

    x_pred = F_h @ x_hat
    P_pred = F_h @ P @ F_h.T + Q_h
    Sigma_h = P_pred[0:2, 0:2]

    # Force strict numerical symmetry on covariance
    P_pred = 0.5 * (P_pred + P_pred.T)
    Sigma_h = 0.5 * (Sigma_h + Sigma_h.T)

    return x_pred, P_pred, Sigma_h

def validate_covariance_properties(P: np.ndarray) -> Dict[str, Any]:
    """
    Validates dimensional consistency, numerical stability, symmetry, and positive-semidefiniteness.
    """
    # 1. Dimensional consistency
    is_square = (P.ndim == 2) and (P.shape[0] == P.shape[1])
    dim = P.shape[0] if is_square else -1

    # 2. Numerical stability
    is_finite = bool(np.all(np.isfinite(P)))

    # 3. Covariance symmetry
    sym_diff = np.max(np.abs(P - P.T)) if is_square else np.inf
    is_symmetric = bool(sym_diff < 1e-8)

    # 4. Positive-semidefiniteness (eigenvalues >= -1e-10)
    if is_square and is_symmetric and is_finite:
        eigvals = np.linalg.eigvalsh(P)
        min_eig = float(np.min(eigvals))
        is_psd = bool(min_eig >= -1e-10)
    else:
        eigvals = np.array([])
        min_eig = np.nan
        is_psd = False

    return {
        "is_square": is_square,
        "dim": dim,
        "is_finite": is_finite,
        "is_symmetric": is_symmetric,
        "symmetry_max_diff": float(sym_diff),
        "is_psd": is_psd,
        "min_eigenvalue": min_eig,
        "eigenvalues": eigvals.tolist() if len(eigvals) > 0 else []
    }

def compute_angular_error_rad(error_px: float, focal_length_px: float = 2000.0) -> float:
    """
    Computes angular prediction error in radians given pixel error and focal length:
    theta = arctan(error_px / f)
    """
    return float(np.arctan(float(error_px) / float(focal_length_px)))
