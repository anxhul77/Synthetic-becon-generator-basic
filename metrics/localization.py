import numpy as np

def compute_localization_errors(x_est: float, y_est: float, x_true: float, y_true: float) -> tuple[float, float, float]:
    """
    Computes individual trial errors:
    e_x = x_est - x_true
    e_y = y_est - y_true
    e_r = sqrt(e_x^2 + e_y^2)
    """
    e_x = float(x_est - x_true)
    e_y = float(y_est - y_true)
    e_r = float(np.sqrt(e_x ** 2 + e_y ** 2))
    return e_x, e_y, e_r

def compute_rmse(errors: np.ndarray) -> float:
    """RMSE = sqrt( (1 / N) * sum(e_i^2) )"""
    return float(np.sqrt(np.mean(np.square(errors))))

def compute_bias(errors: np.ndarray) -> float:
    """Bias = (1 / N) * sum(e_i)"""
    return float(np.mean(errors))

def compute_summary_stats(errors_x: list[float], errors_y: list[float], errors_r: list[float]) -> dict:
    """
    Computes mean, std, median, min, max, RMSE, bias for localization errors.
    """
    arr_x = np.array(errors_x, dtype=np.float64)
    arr_y = np.array(errors_y, dtype=np.float64)
    arr_r = np.array(errors_r, dtype=np.float64)

    return {
        "rmse_x": compute_rmse(arr_x),
        "rmse_y": compute_rmse(arr_y),
        "rmse_radial": compute_rmse(arr_r),
        "bias_x": compute_bias(arr_x),
        "bias_y": compute_bias(arr_y),
        "mean_radial": float(np.mean(arr_r)),
        "std_radial": float(np.std(arr_r)),
        "median_radial": float(np.median(arr_r)),
        "min_radial": float(np.min(arr_r)),
        "max_radial": float(np.max(arr_r)),
    }
