import numpy as np

def compute_angular_errors(theta_x_est: float, theta_y_est: float,
                           theta_x_true: float, theta_y_true: float) -> tuple[float, float, float]:
    """
    Computes angular errors in radians:
    e_theta_x = theta_x_est - theta_x_true
    e_theta_y = theta_y_est - theta_y_true
    e_theta = sqrt(e_theta_x^2 + e_theta_y^2)
    """
    e_tx = float(theta_x_est - theta_x_true)
    e_ty = float(theta_y_est - theta_y_true)
    e_t = float(np.sqrt(e_tx ** 2 + e_ty ** 2))
    return e_tx, e_ty, e_t

def radians_to_mrad(rad: float) -> float:
    """Converts radians to milliradians."""
    return rad * 1000.0

def radians_to_arcsec(rad: float) -> float:
    """Converts radians to arcseconds."""
    return np.degrees(rad) * 3600.0
