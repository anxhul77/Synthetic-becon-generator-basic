"""
Shared Metrics Module for Meghavyuha / SIH26169 FSOC PAT Simulator.

Provides standard, mathematically consistent metric calculators across all experiments:
1. Decomposed Error Metrics (ROI Error, Localizer Error True, Localizer Error ROI, E2E Error)
2. RMSE and Statistical Bounds (Mean, Median, P95, P99, 95% CIs)
3. Tracking Performance (Acquisition Time, Reacquisition Time, Lock Retention, Target Loss)
4. Kalman Innovation & NIS Statistics (Cholesky-based NIS, Chi-Square Mahalanobis Coverage)
5. Search & Realtime Profiling Metrics (Configured Area, Realized Coverage, Throughput FPS)
"""

import numpy as np
from scipy.stats import chi2, norm
from typing import Dict, Any, List, Tuple, Optional


def compute_detector_roi_error(roi_center: Tuple[float, float], target_true: Tuple[float, float]) -> float:
    """Computes Detector ROI acquisition error ||ROI_center - target_true|| [px]."""
    return float(np.hypot(roi_center[0] - target_true[0], roi_center[1] - target_true[1]))


def compute_localizer_error_true(estimate: Tuple[float, float], target_true: Tuple[float, float]) -> float:
    """Computes localizer error relative to true target ||estimate - target_true|| [px]."""
    return float(np.hypot(estimate[0] - target_true[0], estimate[1] - target_true[1]))


def compute_localizer_error_roi(estimate: Tuple[float, float], roi_center: Tuple[float, float], local_target_offset: Tuple[float, float]) -> float:
    """Computes localizer error relative to ROI center ||estimate - ROI_center - local_target_offset|| [px]."""
    est_local_x = estimate[0] - roi_center[0]
    est_local_y = estimate[1] - roi_center[1]
    return float(np.hypot(est_local_x - local_target_offset[0], est_local_y - local_target_offset[1]))


def compute_end_to_end_error(estimate: Tuple[float, float], target_true: Tuple[float, float]) -> float:
    """Computes total end-to-end tracking error ||estimate - target_true|| [px]."""
    return float(np.hypot(estimate[0] - target_true[0], estimate[1] - target_true[1]))


def compute_rmse(errors: List[float]) -> float:
    """Computes Root Mean Square Error sqrt(mean(errors^2))."""
    if not errors:
        return np.nan
    err_arr = np.asarray(errors, dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(err_arr))))


def compute_stats_with_ci(data: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """
    Computes mean, std, median, P95, P99, and confidence interval error bound.
    """
    if not data:
        return {"mean": np.nan, "std": np.nan, "median": np.nan, "p95": np.nan, "p99": np.nan, "ci_bound": np.nan}
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    median_val = float(np.median(arr))
    p95_val = float(np.percentile(arr, 95))
    p99_val = float(np.percentile(arr, 99))

    z_stat = norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    ci_bound = float(z_stat * std_val / np.sqrt(n)) if n > 0 else 0.0

    return {
        "mean": mean_val,
        "std": std_val,
        "median": median_val,
        "p95": p95_val,
        "p99": p99_val,
        "ci_bound": ci_bound
    }


def compute_acquisition_time(hit_mask: List[bool], fps: float, min_consecutive: int = 3) -> float:
    """
    Computes acquisition time: time from experiment start until target satisfies tracking criterion for N consecutive frames.
    Returns np.nan if acquisition criterion is never met.
    """
    n = len(hit_mask)
    consec = 0
    for k in range(n):
        if hit_mask[k]:
            consec += 1
            if consec >= min_consecutive:
                # Frame index of lock confirmation
                acq_frame = k
                return float(acq_frame / fps)
        else:
            consec = 0
    return np.nan


def compute_target_loss(hit_mask: List[bool], eligible_mask: Optional[List[bool]] = None) -> Dict[str, float]:
    """
    Computes target loss percentage over eligible (illuminated/in-FOV) frames.
    """
    hits = np.asarray(hit_mask, dtype=bool)
    if eligible_mask is not None:
        elig = np.asarray(eligible_mask, dtype=bool)
    else:
        elig = np.ones_like(hits, dtype=bool)

    total_eligible = int(np.sum(elig))
    if total_eligible == 0:
        return {"loss_count": 0, "total_eligible": 0, "loss_percentage": 0.0}

    loss_count = int(np.sum(elig & (~hits)))
    loss_pct = float((loss_count / total_eligible) * 100.0)

    return {
        "loss_count": loss_count,
        "total_eligible": total_eligible,
        "loss_percentage": loss_pct
    }


def compute_reacquisition_time(
    hit_mask: List[bool],
    fps: float,
    eligible_mask: Optional[List[bool]] = None,
    min_consecutive: int = 3
) -> Any:
    """
    Computes reacquisition time (seconds) from confirmed track loss until tracking criterion is satisfied again.
    Returns 'NOT_APPLICABLE' if target was never lost.
    Returns 'FAILED' if target was lost but never recovered.
    Returns float (seconds) if target was lost and recovered.
    """
    hits = np.asarray(hit_mask, dtype=bool)
    n = len(hits)
    if eligible_mask is not None:
        elig = np.asarray(eligible_mask, dtype=bool)
    else:
        elig = np.ones_like(hits, dtype=bool)

    reacq_durations = []
    has_lost = False
    in_loss = False
    loss_start_frame = 0
    consec_hits = 0

    for k in range(n):
        if not elig[k]:
            continue

        if not hits[k]:
            has_lost = True
            if not in_loss:
                in_loss = True
                loss_start_frame = k
            consec_hits = 0
        else:
            if in_loss:
                consec_hits += 1
                if consec_hits >= min_consecutive:
                    reacq_dur = k - loss_start_frame
                    reacq_durations.append(reacq_dur / fps)
                    in_loss = False
                    consec_hits = 0

    if not has_lost:
        return "NOT_APPLICABLE"
    if not reacq_durations:
        return "FAILED"
    return float(np.mean(reacq_durations))


def compute_lock_retention(hit_mask: List[bool], eligible_mask: Optional[List[bool]] = None) -> float:
    """
    Computes lock retention percentage: tracked frames / eligible frames.
    """
    hits = np.asarray(hit_mask, dtype=bool)
    if eligible_mask is not None:
        elig = np.asarray(eligible_mask, dtype=bool)
    else:
        elig = np.ones_like(hits, dtype=bool)

    total_eligible = int(np.sum(elig))
    if total_eligible == 0:
        return 0.0
    tracked_count = int(np.sum(hits & elig))
    return float((tracked_count / total_eligible) * 100.0)


def compute_lock_breakdown(track_states: List[str]) -> Dict[str, Any]:
    """
    Detailed lock state breakdown per Priority 2 requirements.
    """
    total_frames = len(track_states)
    locked_frames = sum(1 for s in track_states if s == "TRACKING")
    coasting_frames = sum(1 for s in track_states if s == "COASTING")
    searching_frames = sum(1 for s in track_states if s == "SEARCHING")
    reacquiring_frames = sum(1 for s in track_states if s == "REACQUIRING")
    lost_frames = sum(1 for s in track_states if s == "LOST")

    lock_retention_pct = (locked_frames / max(1, total_frames)) * 100.0
    return {
        "total_frames": total_frames,
        "locked_frames": locked_frames,
        "coasting_frames": coasting_frames,
        "searching_frames": searching_frames,
        "reacquiring_frames": reacquiring_frames,
        "lost_frames": lost_frames,
        "lock_retention_pct": float(lock_retention_pct)
    }



def compute_nis_cholesky(y_innov: np.ndarray, S_cov: np.ndarray) -> float:
    """
    Computes Normalized Innovation Squared (NIS): nu^T * inv(S) * nu
    using fast matrix solve for numerical stability.
    """
    y = np.asarray(y_innov, dtype=np.float64).ravel()
    S = np.asarray(S_cov, dtype=np.float64)

    try:
        sol = np.linalg.solve(S, y)
        nis_val = float(y @ sol)
        return nis_val
    except Exception:
        try:
            S_inv = np.linalg.pinv(S)
            nis_val = float(y @ S_inv @ y)
            return nis_val
        except Exception:
            return 999.0


def compute_mahalanobis_coverage(nis_values: List[float], df: int = 2) -> Dict[str, Any]:
    """
    Computes empirical Mahalanobis coverage at 50%, 90%, and 95% Chi-Square thresholds.
    Returns empirical coverage percentages and calibration verdict.
    """
    if not nis_values:
        return {
            "mean_nis": np.nan,
            "coverage_50_pct": np.nan,
            "coverage_90_pct": np.nan,
            "coverage_95_pct": np.nan,
            "verdict": "NO_DATA"
        }

    nis_arr = np.asarray(nis_values, dtype=np.float64)
    n = len(nis_arr)
    mean_nis = float(np.mean(nis_arr))

    # Theoretical Chi2 thresholds for df=2
    gate_50 = chi2.ppf(0.50, df=df)  # 1.3863
    gate_90 = chi2.ppf(0.90, df=df)  # 4.6052
    gate_95 = chi2.ppf(0.95, df=df)  # 5.9915

    cov_50 = float(np.sum(nis_arr <= gate_50) / n * 100.0)
    cov_90 = float(np.sum(nis_arr <= gate_90) / n * 100.0)
    cov_95 = float(np.sum(nis_arr <= gate_95) / n * 100.0)

    # Calibration verdict logic:
    # Theoretical mean NIS for Chi2(2) is 2.0.
    if mean_nis > 4.0 or cov_95 < 85.0:
        verdict = "UNDER_DISPERSED"  # Covariance is too small (under-estimated uncertainty)
    elif mean_nis < 0.8 or cov_50 > 75.0:
        verdict = "OVER_DISPERSED"   # Covariance is too large (over-estimated uncertainty)
    else:
        verdict = "APPROXIMATELY_CALIBRATED"

    return {
        "mean_nis": mean_nis,
        "coverage_50_pct": cov_50,
        "coverage_90_pct": cov_90,
        "coverage_95_pct": cov_95,
        "verdict": verdict
    }


def compute_throughput_fps(total_latency_ms: float) -> float:
    """Computes throughput FPS = 1000.0 / total_loop_latency_ms."""
    if total_latency_ms <= 0:
        return 0.0
    return float(1000.0 / total_latency_ms)
