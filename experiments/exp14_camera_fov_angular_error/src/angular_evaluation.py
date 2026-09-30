import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from generator.camera import PinholeCamera

def compute_exact_angular_pointing_error(
    x_est: float,
    y_est: float,
    x_true: float,
    y_true: float,
    camera: PinholeCamera
) -> Dict[str, Any]:
    """
    Computes exact angular pointing errors e_theta in radians and microradians (urad)
    using non-linear pinhole camera projections:
    theta_x = arctan((u - c_x) / f_x)
    theta_y = arctan((v - c_y) / f_y)
    e_theta = sqrt((hat_theta_x - theta_x_true)^2 + (hat_theta_y - theta_y_true)^2)
    """
    if x_est is None or y_est is None or np.isnan(x_est) or np.isnan(y_est):
        return {
            "theta_x_true_rad": None,
            "theta_y_true_rad": None,
            "theta_x_est_rad": None,
            "theta_y_est_rad": None,
            "angular_error_x_rad": None,
            "angular_error_y_rad": None,
            "angular_error_rad": None,
            "angular_error_urad": None,
            "angular_error_arcsec": None
        }

    # True angles
    tx_true, ty_true = camera.pixel_to_angle(x_true, y_true)
    # Estimated angles
    tx_est, ty_est = camera.pixel_to_angle(x_est, y_est)

    # Errors in radians
    e_tx = float(tx_est - tx_true)
    e_ty = float(ty_est - ty_true)
    e_theta_rad = float(np.sqrt(e_tx ** 2 + e_ty ** 2))
    e_theta_urad = float(e_theta_rad * 1e6)
    e_theta_arcsec = float(e_theta_rad * (180.0 / np.pi) * 3600.0)

    return {
        "theta_x_true_rad": float(tx_true),
        "theta_y_true_rad": float(ty_true),
        "theta_x_est_rad": float(tx_est),
        "theta_y_est_rad": float(ty_est),
        "angular_error_x_rad": e_tx,
        "angular_error_y_rad": e_ty,
        "angular_error_rad": e_theta_rad,
        "angular_error_urad": e_theta_urad,
        "angular_error_arcsec": e_theta_arcsec
    }


def compute_fov_metrics(camera: PinholeCamera) -> Dict[str, float]:
    """
    Computes camera Field of View (FOV) parameters in degrees and angular resolution scale in urad/px.
    """
    w, h = camera.width, camera.height
    fx, fy = camera.fx, camera.fy

    fov_x_deg = float(2.0 * np.arctan(w / (2.0 * fx)) * (180.0 / np.pi))
    fov_y_deg = float(2.0 * np.arctan(h / (2.0 * fy)) * (180.0 / np.pi))
    fov_diag_deg = float(2.0 * np.arctan(np.sqrt(w**2 + h**2) / (2.0 * fx)) * (180.0 / np.pi))

    # Paraxial center scale: urad per pixel
    scale_center_urad_per_px = float((1.0 / fx) * 1e6)

    return {
        "fov_x_deg": fov_x_deg,
        "fov_y_deg": fov_y_deg,
        "fov_diag_deg": fov_diag_deg,
        "scale_center_urad_per_px": scale_center_urad_per_px,
        "focal_length_px": float(fx)
    }


def compute_off_axis_scale_factor(x_true: float, y_true: float, camera: PinholeCamera) -> float:
    """
    Computes local differential scale factor d(theta)/dp = 1 / (f * (1 + (p - c)^2 / f^2))
    showing off-axis arctan compression compared to center.
    """
    r_sq = (x_true - camera.cx)**2 + (y_true - camera.cy)**2
    compression = 1.0 / (1.0 + r_sq / (camera.fx ** 2))
    return float(compression)
