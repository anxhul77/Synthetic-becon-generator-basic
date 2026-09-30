import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from generator.camera import PinholeCamera

def compute_pixel_and_angular_errors(
    x_est: Optional[float],
    y_est: Optional[float],
    x_true: float,
    y_true: float,
    camera: PinholeCamera
) -> Dict[str, Optional[float]]:
    """
    Computes subpixel localization errors and exact pinhole camera angular errors.
    Returns dictionary with error_x, error_y, radial_error,
    angular_error_x, angular_error_y, angular_error_mag (in radians and microradians).
    """
    if x_est is None or y_est is None or np.isnan(x_est) or np.isnan(y_est):
        return {
            "error_x": None,
            "error_y": None,
            "radial_error": None,
            "angular_error_x_rad": None,
            "angular_error_y_rad": None,
            "angular_error_rad": None,
            "angular_error_urad": None
        }

    err_x = float(x_est - x_true)
    err_y = float(y_est - y_true)
    radial_err = float(np.sqrt(err_x ** 2 + err_y ** 2))

    tx_est, ty_est = camera.pixel_to_angle(x_est, y_est)
    tx_true, ty_true = camera.pixel_to_angle(x_true, y_true)

    d_tx = float(tx_est - tx_true)
    d_ty = float(ty_est - ty_true)
    ang_err_rad = float(np.sqrt(d_tx ** 2 + d_ty ** 2))
    ang_err_urad = float(ang_err_rad * 1e6)

    return {
        "error_x": err_x,
        "error_y": err_y,
        "radial_error": radial_err,
        "angular_error_x_rad": d_tx,
        "angular_error_y_rad": d_ty,
        "angular_error_rad": ang_err_rad,
        "angular_error_urad": ang_err_urad
    }

def compute_group_summary_stats(df_group: pd.DataFrame, num_bootstraps: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Computes statistical metrics (accuracy, bias, success rate, latency, CIs) for a group of trials.
    Handles failed trials explicitly.
    """
    total_trials = len(df_group)
    if total_trials == 0:
        return {}

    successful_trials = df_group[df_group["success"] == True]
    success_count = len(successful_trials)
    success_rate = float(success_count / total_trials)

    mean_latency = float(df_group["runtime_ms"].mean())
    median_latency = float(df_group["runtime_ms"].median())
    p95_latency = float(np.percentile(df_group["runtime_ms"], 95)) if total_trials > 0 else 0.0

    if success_count == 0:
        return {
            "total_trials": total_trials,
            "success_count": 0,
            "success_rate": 0.0,
            "mean_radial_error": np.nan,
            "median_radial_error": np.nan,
            "std_radial_error": np.nan,
            "radial_rmse": np.nan,
            "p95_radial_error": np.nan,
            "max_radial_error": np.nan,
            "bias_x": np.nan,
            "bias_y": np.nan,
            "bias_magnitude": np.nan,
            "angular_rmse_urad": np.nan,
            "mean_latency_ms": mean_latency,
            "median_latency_ms": median_latency,
            "p95_latency_ms": p95_latency,
            "rmse_ci_lower": np.nan,
            "rmse_ci_upper": np.nan
        }

    err_x = successful_trials["error_x"].values.astype(np.float64)
    err_y = successful_trials["error_y"].values.astype(np.float64)
    err_r = successful_trials["radial_error"].values.astype(np.float64)
    ang_r_urad = successful_trials["angular_error_urad"].values.astype(np.float64)

    mean_r = float(np.mean(err_r))
    med_r = float(np.median(err_r))
    std_r = float(np.std(err_r))
    rmse_x = float(np.sqrt(np.mean(err_x ** 2)))
    rmse_y = float(np.sqrt(np.mean(err_y ** 2)))
    rmse_r = float(np.sqrt(np.mean(err_r ** 2)))
    p95_r = float(np.percentile(err_r, 95))
    max_r = float(np.max(err_r))

    bias_x = float(np.mean(err_x))
    bias_y = float(np.mean(err_y))
    bias_mag = float(np.sqrt(bias_x ** 2 + bias_y ** 2))

    ang_rmse_urad = float(np.sqrt(np.mean(ang_r_urad ** 2)))

    # Bootstrap 95% CI for Radial RMSE
    ci_lower, ci_upper = compute_bootstrap_ci(err_r, metric_fn=lambda arr: np.sqrt(np.mean(arr ** 2)), num_bootstraps=num_bootstraps, seed=seed)

    return {
        "total_trials": total_trials,
        "success_count": success_count,
        "success_rate": success_rate,
        "mean_radial_error": mean_r,
        "median_radial_error": med_r,
        "std_radial_error": std_r,
        "rmse_x": rmse_x,
        "rmse_y": rmse_y,
        "radial_rmse": rmse_r,
        "p95_radial_error": p95_r,
        "max_radial_error": max_r,
        "bias_x": bias_x,
        "bias_y": bias_y,
        "bias_magnitude": bias_mag,
        "angular_rmse_urad": ang_rmse_urad,
        "mean_latency_ms": mean_latency,
        "median_latency_ms": median_latency,
        "p95_latency_ms": p95_latency,
        "rmse_ci_lower": ci_lower,
        "rmse_ci_upper": ci_upper
    }


def compute_bootstrap_ci(arr: np.ndarray, metric_fn, num_bootstraps: int = 1000, confidence: float = 0.95, seed: int = 42) -> tuple[float, float]:
    """Computes percentile bootstrap confidence interval for a metric function over an array."""
    if len(arr) < 2:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    n = len(arr)
    boots = np.empty(num_bootstraps, dtype=np.float64)
    for i in range(num_bootstraps):
        resample = rng.choice(arr, size=n, replace=True)
        boots[i] = metric_fn(resample)
    alpha = 1.0 - confidence
    lower_pct = (alpha / 2.0) * 100.0
    upper_pct = (1.0 - alpha / 2.0) * 100.0
    return float(np.percentile(boots, lower_pct)), float(np.percentile(boots, upper_pct))

def compute_paired_comparison(df_raw: pd.DataFrame, method_a: str, method_b: str, num_bootstraps: int = 1000, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Computes paired statistical differences between method_a and method_b across shared images/trials.
    Includes trial identity preservation and bootstrap 95% CIs.
    """
    paired_rows = []
    # Group by experimental condition keys
    group_cols = [c for c in ["scenario_id", "snr_db", "background_level", "psf_condition", "roi_size", "subpixel_offset"] if c in df_raw.columns]

    for cond_vals, group in df_raw.groupby(group_cols):
        df_a = group[group["method_name"] == method_a].set_index("trial_id")
        df_b = group[group["method_name"] == method_b].set_index("trial_id")

        common_trials = df_a.index.intersection(df_b.index)
        if len(common_trials) == 0:
            continue

        sub_a = df_a.loc[common_trials]
        sub_b = df_b.loc[common_trials]

        # Filter to trials where BOTH methods succeeded
        both_succ = (sub_a["success"] == True) & (sub_b["success"] == True)
        valid_a = sub_a[both_succ]
        valid_b = sub_b[both_succ]

        paired_count = len(valid_a)
        if paired_count == 0:
            rmse_diff = np.nan
            mean_diff = np.nan
            ci_lower, ci_upper = np.nan, np.nan
            lat_diff = float(sub_b["runtime_ms"].mean() - sub_a["runtime_ms"].mean())
        else:
            err_r_a = valid_a["radial_error"].values.astype(np.float64)
            err_r_b = valid_b["radial_error"].values.astype(np.float64)

            rmse_a = np.sqrt(np.mean(err_r_a ** 2))
            rmse_b = np.sqrt(np.mean(err_r_b ** 2))
            rmse_diff = float(rmse_b - rmse_a)

            mean_a = np.mean(err_r_a)
            mean_b = np.mean(err_r_b)
            mean_diff = float(mean_b - mean_a)

            lat_diff = float(valid_b["runtime_ms"].mean() - valid_a["runtime_ms"].mean())

            # Paired bootstrap for RMSE difference
            rng = np.random.default_rng(seed)
            diff_boots = np.empty(num_bootstraps, dtype=np.float64)
            for b in range(num_bootstraps):
                idx = rng.choice(paired_count, size=paired_count, replace=True)
                r_a_b = err_r_a[idx]
                r_b_b = err_r_b[idx]
                rmse_a_b = np.sqrt(np.mean(r_a_b ** 2))
                rmse_b_b = np.sqrt(np.mean(r_b_b ** 2))
                diff_boots[b] = rmse_b_b - rmse_a_b

            ci_lower = float(np.percentile(diff_boots, 2.5))
            ci_upper = float(np.percentile(diff_boots, 97.5))

        cond_dict = dict(zip(group_cols, cond_vals if isinstance(cond_vals, tuple) else [cond_vals]))
        row = {
            **cond_dict,
            "method_a": method_a,
            "method_b": method_b,
            "paired_trial_count": paired_count,
            "rmse_difference": rmse_diff,
            "mean_error_difference": mean_diff,
            "ci_lower_diff": ci_lower,
            "ci_upper_diff": ci_upper,
            "latency_difference_ms": lat_diff
        }
        paired_rows.append(row)

    return paired_rows
