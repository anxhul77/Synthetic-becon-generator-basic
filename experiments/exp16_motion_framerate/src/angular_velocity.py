import numpy as np
from typing import Dict, Any

def angular_velocity_to_pixel_velocity(
    omega_deg_per_sec: float,
    focal_length_px: float = 2000.0
) -> float:
    """
    Converts beacon angular velocity omega (deg/s) into focal plane pixel velocity (px/s)
    using pinhole optics: v_px_per_sec = f * tan(omega_rad_per_sec)
    """
    omega_rad_per_sec = float(np.deg2rad(omega_deg_per_sec))
    v_px_per_sec = float(focal_length_px * np.tan(omega_rad_per_sec))
    return v_px_per_sec

def compute_interframe_displacement(
    omega_deg_per_sec: float,
    fps: float,
    focal_length_px: float = 2000.0
) -> Dict[str, float]:
    """
    Computes inter-frame displacement Delta s (px/frame) and angular displacement per frame.
    """
    v_px_per_sec = angular_velocity_to_pixel_velocity(omega_deg_per_sec, focal_length_px)
    delta_s_px = float(v_px_per_sec / fps)
    omega_per_frame_deg = float(omega_deg_per_sec / fps)
    omega_per_frame_urad = float(np.deg2rad(omega_per_frame_deg) * 1e6)

    return {
        "omega_deg_per_sec": float(omega_deg_per_sec),
        "fps": float(fps),
        "focal_length_px": float(focal_length_px),
        "v_px_per_sec": v_px_per_sec,
        "delta_s_px_per_frame": delta_s_px,
        "omega_per_frame_deg": omega_per_frame_deg,
        "omega_per_frame_urad": omega_per_frame_urad
    }
