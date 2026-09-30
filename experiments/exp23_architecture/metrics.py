import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def compute_architecture_summary(df_raw: pd.DataFrame, architecture_name: str) -> Dict[str, Any]:
    """
    Calculates summary latency, throughput, detection, and localization statistics for a given architecture.
    """
    sub_df = df_raw[df_raw["architecture"] == architecture_name].copy()
    if len(sub_df) == 0:
        return {}

    latencies = sub_df["end_to_end_latency_ms"].values
    mean_lat = float(np.mean(latencies))
    median_lat = float(np.median(latencies))
    std_lat = float(np.std(latencies))
    p90_lat = float(np.percentile(latencies, 90))
    p95_lat = float(np.percentile(latencies, 95))
    p99_lat = float(np.percentile(latencies, 99))
    min_lat = float(np.min(latencies))
    max_lat = float(np.max(latencies))

    fps_latency = 1000.0 / mean_lat if mean_lat > 0 else 0.0

    # Detection correctness
    n_frames = len(sub_df)
    n_detected = int(sub_df["detected"].sum())
    p_detection = float(n_detected / n_frames) if n_frames > 0 else 0.0

    det_df = sub_df[sub_df["detected"] == 1]
    if len(det_df) > 0 and "x_true" in det_df.columns:
        err_x = det_df["x_est"].values - det_df["x_true"].values
        err_y = det_df["y_est"].values - det_df["y_true"].values
        radial_err = np.sqrt(err_x**2 + err_y**2)
        rmse_px = float(np.sqrt(np.mean(radial_err**2)))
        bias_x = float(np.mean(err_x))
        bias_y = float(np.mean(err_y))
    else:
        rmse_px = np.nan
        bias_x = np.nan
        bias_y = np.nan

    return {
        "architecture": architecture_name,
        "total_frames": n_frames,
        "mean_latency_ms": mean_lat,
        "median_latency_ms": median_lat,
        "std_latency_ms": std_lat,
        "p90_latency_ms": p90_lat,
        "p95_latency_ms": p95_lat,
        "p99_latency_ms": p99_lat,
        "min_latency_ms": min_lat,
        "max_latency_ms": max_lat,
        "latency_based_fps": fps_latency,
        "detection_probability": p_detection,
        "localization_rmse_px": rmse_px,
        "bias_x_px": bias_x,
        "bias_y_px": bias_y
    }

def compute_paired_comparison_metrics(df_seq: pd.DataFrame,
                                       df_par: pd.DataFrame,
                                       num_bootstraps: int = 1000,
                                       seed: int = 42) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes paired frame latency differences and bootstrap 95% confidence intervals.
    """
    merged = pd.merge(
        df_seq[["frame_id", "end_to_end_latency_ms", "detected", "x_est", "y_est"]],
        df_par[["frame_id", "end_to_end_latency_ms", "detected", "x_est", "y_est"]],
        on="frame_id",
        suffixes=("_seq", "_par")
    )

    merged["latency_difference_ms"] = merged["end_to_end_latency_ms_seq"] - merged["end_to_end_latency_ms_par"]
    merged["per_frame_speedup"] = merged["end_to_end_latency_ms_seq"] / np.maximum(1e-6, merged["end_to_end_latency_ms_par"])

    diffs = merged["latency_difference_ms"].values
    mean_diff = float(np.mean(diffs))
    median_diff = float(np.median(diffs))

    seq_lat = merged["end_to_end_latency_ms_seq"].values
    par_lat = merged["end_to_end_latency_ms_par"].values
    mean_speedup = float(np.mean(seq_lat) / np.mean(par_lat))
    median_speedup = float(np.median(seq_lat) / np.median(par_lat))

    # Bootstrap CIs
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot_diffs = []
    boot_speedups = []

    for _ in range(num_bootstraps):
        idxs = rng.choice(n, size=n, replace=True)
        b_diff = np.mean(diffs[idxs])
        b_speedup = np.mean(seq_lat[idxs]) / np.maximum(1e-6, np.mean(par_lat[idxs]))
        boot_diffs.append(b_diff)
        boot_speedups.append(b_speedup)

    diff_ci_low, diff_ci_high = float(np.percentile(boot_diffs, 2.5)), float(np.percentile(boot_diffs, 97.5))
    speedup_ci_low, speedup_ci_high = float(np.percentile(boot_speedups, 2.5)), float(np.percentile(boot_speedups, 97.5))

    fraction_parallel_faster = float(np.mean(diffs > 0))

    summary = {
        "num_paired_frames": len(merged),
        "mean_latency_seq_ms": float(np.mean(seq_lat)),
        "mean_latency_par_ms": float(np.mean(par_lat)),
        "mean_paired_difference_ms": mean_diff,
        "median_paired_difference_ms": median_diff,
        "difference_ci95_low_ms": diff_ci_low,
        "difference_ci95_high_ms": diff_ci_high,
        "mean_speedup": mean_speedup,
        "median_speedup": median_speedup,
        "speedup_ci95_low": speedup_ci_low,
        "speedup_ci95_high": speedup_ci_high,
        "fraction_parallel_faster": fraction_parallel_faster
    }

    return merged, summary
