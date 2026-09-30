import numpy as np
from typing import Tuple, Dict, Any, List

def compute_innovation_nis(
    z_k: np.ndarray,
    x_pred: np.ndarray,
    P_pred: np.ndarray,
    H: np.ndarray,
    R: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Computes observable measurement innovation nu_k = z_k - H*x_pred,
    innovation covariance S_k = H*P_pred*H^T + R, and Normalized Innovation Squared NIS_k.
    """
    z_k = np.asarray(z_k, dtype=np.float64)
    x_pred = np.asarray(x_pred, dtype=np.float64)

    nu_k = z_k - (H @ x_pred)
    S_k = H @ P_pred @ H.T + R
    S_inv = np.linalg.inv(S_k)

    nis_k = float(nu_k.T @ S_inv @ nu_k)
    return nu_k, S_k, max(0.0, nis_k)

def compute_error_adapted_amplitude(
    sigma_val: float,
    gamma: float,
    nis_stat: float,
    lambda_adapt: float,
    A_max: float
) -> float:
    """
    Computes observable residual-adapted search amplitude:
    A_i = min(A_max, gamma * sigma_i + lambda_adapt * sqrt(nis_stat))
    """
    g_i = np.sqrt(max(0.0, nis_stat))
    A_requested = gamma * sigma_val + lambda_adapt * g_i
    return float(np.clip(A_requested, 0.0, A_max))

def generate_error_adaptive_eal(
    cx: float,
    cy: float,
    Sigma_5: np.ndarray,
    nis_history: List[float],
    gamma: float = 2.4477,
    lambda_adapt: float = 12.5,
    A_max: float = 350.0,
    duration_sec: float = 5.0,
    fps: float = 30.0,
    w1: float = 3.0 * np.pi,
    w2: float = 2.0 * np.pi,
    phi1: float = 0.0,
    phi2: float = np.pi / 2.0,
    width: float = 1920.0,
    height: float = 1080.0
) -> Dict[str, np.ndarray]:
    """
    Generates Error-Adaptive Lissajous search trajectory using observable innovation NIS feedback.
    """
    num_samples = int(duration_sec * fps)
    t = np.linspace(0.0, duration_sec, num_samples)
    dt = 1.0 / fps

    # Compute moving average of recent NIS history
    if len(nis_history) > 0:
        recent_nis = np.mean(nis_history[-5:])
    else:
        recent_nis = 1.0

    eigvals, eigvecs = np.linalg.eigh(Sigma_5)
    idx = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(1e-6, eigvals[idx])
    eigvecs = eigvecs[:, idx]

    l1, l2 = eigvals[0], eigvals[1]

    # Compute residual-adapted amplitudes along principal axes
    A1 = compute_error_adapted_amplitude(np.sqrt(l1), gamma, recent_nis, lambda_adapt, A_max)
    A2 = compute_error_adapted_amplitude(np.sqrt(l2), gamma, recent_nis, lambda_adapt, A_max)

    scale = t / duration_sec

    x_local = A1 * scale * np.sin(w1 * t + phi1)
    y_local = A2 * scale * np.sin(w2 * t + phi2)
    local_coords = np.vstack([x_local, y_local])

    rotated_coords = eigvecs @ local_coords

    u_search = np.clip(cx + rotated_coords[0, :], 0.0, width)
    v_search = np.clip(cy + rotated_coords[1, :], 0.0, height)

    du = np.gradient(u_search, dt)
    dv = np.gradient(v_search, dt)
    vel = np.sqrt(du**2 + dv**2)

    d2u = np.gradient(du, dt)
    d2v = np.gradient(dv, dt)
    accel = np.sqrt(d2u**2 + d2v**2)

    return {
        "time": t,
        "u": u_search,
        "v": v_search,
        "velocity": vel,
        "acceleration": accel,
        "A1": A1,
        "A2": A2,
        "nis_stat": float(recent_nis)
    }
