import numpy as np
from typing import Tuple, Dict, Any, Optional

def generate_fixed_eal(
    cx: float,
    cy: float,
    A_fixed: float = 150.0,
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
    Generates Fixed Expanding Amplitude Lissajous (EAL) search trajectory.
    """
    num_samples = int(duration_sec * fps)
    t = np.linspace(0.0, duration_sec, num_samples)
    dt = 1.0 / fps

    # Linear amplitude expansion scaling factor [0, 1]
    scale = t / duration_sec

    u_raw = A_fixed * scale * np.sin(w1 * t + phi1)
    v_raw = A_fixed * scale * np.sin(w2 * t + phi2)

    u_search = np.clip(cx + u_raw, 0.0, width)
    v_search = np.clip(cy + v_raw, 0.0, height)

    # Compute trajectory velocity and acceleration
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
        "A1": A_fixed,
        "A2": A_fixed
    }

def generate_adaptive_eal(
    cx: float,
    cy: float,
    Sigma_5: np.ndarray,
    gamma: float = 2.4477,
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
    Generates Uncertainty-Adaptive EAL search trajectory aligned with 5-second position covariance \Sigma_5.
    """
    num_samples = int(duration_sec * fps)
    t = np.linspace(0.0, duration_sec, num_samples)
    dt = 1.0 / fps

    # Eigen-decomposition of 2x2 position covariance
    eigvals, eigvecs = np.linalg.eigh(Sigma_5)
    idx = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(1e-6, eigvals[idx])
    eigvecs = eigvecs[:, idx]

    l1, l2 = eigvals[0], eigvals[1]

    # Covariance-scaled semi-axes
    A1 = gamma * np.sqrt(l1)
    A2 = gamma * np.sqrt(l2)

    scale = t / duration_sec

    # Ellipse-local expanding Lissajous coordinates
    x_local = A1 * scale * np.sin(w1 * t + phi1)
    y_local = A2 * scale * np.sin(w2 * t + phi2)

    local_coords = np.vstack([x_local, y_local])  # 2 x N

    # Rotate by covariance eigenvectors V
    rotated_coords = eigvecs @ local_coords  # 2 x N

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
        "eigenvalues": eigvals,
        "eigenvectors": eigvecs
    }

def check_acquisition(
    search_u: np.ndarray,
    search_v: np.ndarray,
    target_u: np.ndarray,
    target_v: np.ndarray,
    acq_radius: float = 15.0,
    consec_frames: int = 3,
    fps: float = 30.0
) -> Tuple[Optional[int], Optional[float]]:
    """
    Checks if beacon is acquired during search trajectory.
    Acquisition criterion: target distance <= acq_radius for consec_frames consecutive frames.
    Returns (acq_frame_index, acq_time_sec).
    """
    num_frames = min(len(search_u), len(target_u))
    dists = np.sqrt((search_u[:num_frames] - target_u[:num_frames])**2 +
                    (search_v[:num_frames] - target_v[:num_frames])**2)

    in_gate = dists <= acq_radius

    consec_count = 0
    for k in range(num_frames):
        if in_gate[k]:
            consec_count += 1
            if consec_count >= consec_frames:
                acq_frame = k
                acq_time = acq_frame / fps
                return acq_frame, float(acq_time)
        else:
            consec_count = 0

    return None, None

def compute_search_path_length(u: np.ndarray, v: np.ndarray) -> float:
    """
    Computes cumulative spatial search path length L_search = sum ||p_{i+1} - p_i||.
    """
    du = np.diff(u)
    dv = np.diff(v)
    step_lens = np.sqrt(du**2 + dv**2)
    return float(np.sum(step_lens))
