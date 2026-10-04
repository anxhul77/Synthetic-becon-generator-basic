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
    # 1. True angles & Beacon Angular Displacement (e_beacon) - Always valid
    tx_true, ty_true = camera.pixel_to_angle(x_true, y_true)
    beacon_ang_rad = float(np.sqrt(tx_true**2 + ty_true**2))
    beacon_ang_urad = float(beacon_ang_rad * 1e6)

    if x_est is None or y_est is None or np.isnan(x_est) or np.isnan(y_est):
        return {
            "pixel_localization_error_px": None,
            "theta_x_true_rad": float(tx_true),
            "theta_y_true_rad": float(ty_true),
            "theta_x_est_rad": None,
            "theta_y_est_rad": None,
            "angular_error_x_rad": None,
            "angular_error_y_rad": None,
            "angular_error_rad": None,
            "angular_error_urad": None,
            "angular_error_arcsec": None,
            "camera_pointing_error_urad": None,
            "beacon_angular_error_urad": beacon_ang_urad,
            "ptz_command_error_urad_5deg_s": None,
            "ptz_command_error_urad_10deg_s": None
        }

    # 2. Pixel Localization Error (e_px) & Estimated Angles
    err_x_px = float(x_est - x_true)
    err_y_px = float(y_est - y_true)
    e_px = float(np.sqrt(err_x_px**2 + err_y_px**2))

    tx_est, ty_est = camera.pixel_to_angle(x_est, y_est)
    e_tx = float(tx_est - tx_true)
    e_ty = float(ty_est - ty_true)
    e_theta_rad = float(np.sqrt(e_tx ** 2 + e_ty ** 2))
    e_theta_urad = float(e_theta_rad * 1e6)
    e_theta_arcsec = float(e_theta_rad * (180.0 / np.pi) * 3600.0)

    # 4. PTZ Command Error given 30 Hz update rate and speed limits (5 deg/s and 10 deg/s)
    fps = camera.fps if camera.fps > 0 else 30.0
    dt = 1.0 / fps
    max_step_rad_5 = float(np.radians(5.0 * dt))
    max_step_rad_10 = float(np.radians(10.0 * dt))

    e_ptz_rad_5 = float(max(0.0, e_theta_rad - max_step_rad_5))
    e_ptz_rad_10 = float(max(0.0, e_theta_rad - max_step_rad_10))

    e_ptz_urad_5 = float(e_ptz_rad_5 * 1e6)
    e_ptz_urad_10 = float(e_ptz_rad_10 * 1e6)

    return {
        "pixel_localization_error_px": e_px,
        "theta_x_true_rad": float(tx_true),
        "theta_y_true_rad": float(ty_true),
        "theta_x_est_rad": float(tx_est),
        "theta_y_est_rad": float(ty_est),
        "angular_error_x_rad": e_tx,
        "angular_error_y_rad": e_ty,
        "angular_error_rad": e_theta_rad,
        "angular_error_urad": e_theta_urad,
        "angular_error_arcsec": e_theta_arcsec,
        "camera_pointing_error_urad": e_theta_urad,
        "beacon_angular_error_urad": beacon_ang_urad,
        "ptz_command_error_urad_5deg_s": e_ptz_urad_5,
        "ptz_command_error_urad_10deg_s": e_ptz_urad_10
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
