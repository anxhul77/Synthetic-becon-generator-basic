import numpy as np
import pandas as pd

def compute_wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Computes Wilson score 95% confidence interval for a proportion p with n trials.
    """
    if n <= 0:
        return 0.0, 0.0
    denominator = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2.0 * n)) / denominator
    spread = z * np.sqrt((p * (1.0 - p) / n) + (z ** 2) / (4.0 * (n ** 2))) / denominator
    lower = max(0.0, float(center - spread))
    upper = min(1.0, float(center + spread))
    return lower, upper

def compute_paired_bootstrap_ci(vec_a: np.ndarray,
                                vec_b: np.ndarray,
                                num_bootstraps: int = 1000,
                                ci_level: float = 0.95,
                                seed: int = 42) -> tuple[float, float, float]:
    """
    Computes paired bootstrap difference (mean(A) - mean(B)) and 95% confidence intervals.
    """
    if len(vec_a) == 0 or len(vec_b) == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)
    n = len(vec_a)
    diffs = []

    for _ in range(num_bootstraps):
        idxs = rng.integers(0, n, size=n)
        mean_a = np.mean(vec_a[idxs])
        mean_b = np.mean(vec_b[idxs])
        diffs.append(mean_a - mean_b)

    diffs = np.array(diffs)
    mean_diff = float(np.mean(diffs))
    alpha = (1.0 - ci_level) / 2.0
    lower = float(np.percentile(diffs, alpha * 100.0))
    upper = float(np.percentile(diffs, (1.0 - alpha) * 100.0))

    return mean_diff, lower, upper

def evaluate_predictions(df_predictions: pd.DataFrame, tolerance_px: float = 5.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes summary metrics (PD, PFA, Precision, Recall, F1, RMSE, Latency)
    and paired differences across detectors (Classical, AI, Hybrid).
    """
    detectors = df_predictions["detector"].unique()
    conditions = df_predictions["scenario_id"].unique()

    summary_rows = []

    for cond in conditions:
        sub_cond = df_predictions[df_predictions["scenario_id"] == cond]
        
        for det in detectors:
            sub = sub_cond[sub_cond["detector"] == det]
            if len(sub) == 0:
                continue

            # Beacon present images
            beacon_present_df = sub[sub["beacon_present"] == True]
            n_present = len(beacon_present_df)
            tp = int(((beacon_present_df["detected"] == True) & (beacon_present_df["localization_error_px"] <= tolerance_px)).sum())
            fn = n_present - tp
            pd_val = float(tp / n_present) if n_present > 0 else 0.0
            pd_low, pd_high = compute_wilson_ci(pd_val, n_present)

            # Beacon absent images
            beacon_absent_df = sub[sub["beacon_present"] == False]
            n_absent = len(beacon_absent_df)
            fp_images = int((beacon_absent_df["detected"] == True).sum())
            pfa_val = float(fp_images / n_absent) if n_absent > 0 else 0.0
            pfa_low, pfa_high = compute_wilson_ci(pfa_val, n_absent)

            # False candidate counts per image
            mean_false_cands = float(sub["false_candidate_count"].mean()) if "false_candidate_count" in sub else 0.0

            # Total predictions & false positives for Precision/Recall/F1
            fp_total = int(((sub["detected"] == True) & ((sub["beacon_present"] == False) | (sub["localization_error_px"] > tolerance_px))).sum())
            precision = float(tp / (tp + fp_total)) if (tp + fp_total) > 0 else 0.0
            recall = pd_val
            f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            # Localization RMSE
            valid_loc_errors = beacon_present_df.loc[beacon_present_df["localization_error_px"].notna() & (beacon_present_df["localization_error_px"] <= tolerance_px), "localization_error_px"]
            rmse_val = float(np.sqrt(np.mean(valid_loc_errors ** 2))) if len(valid_loc_errors) > 0 else np.nan

            # Latency metrics
            latency_mean = float(sub["total_latency_ms"].mean()) if "total_latency_ms" in sub else 0.0
            latency_p95 = float(np.percentile(sub["total_latency_ms"], 95)) if "total_latency_ms" in sub else 0.0
            fps_val = float(1000.0 / latency_mean) if latency_mean > 0 else 0.0

            summary_rows.append({
                "scenario_id": cond,
                "detector": det,
                "n_present": n_present,
                "n_absent": n_absent,
                "tp": tp,
                "fn": fn,
                "fp_images": fp_images,
                "pd": pd_val,
                "pd_ci_low": pd_low,
                "pd_ci_high": pd_high,
                "pfa": pfa_val,
                "pfa_ci_low": pfa_low,
                "pfa_ci_high": pfa_high,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "mean_false_candidates": mean_false_cands,
                "rmse_px": rmse_val,
                "latency_mean_ms": latency_mean,
                "latency_p95_ms": latency_p95,
                "fps": fps_val
            })

    df_summary = pd.DataFrame(summary_rows)

    # Paired comparisons against Classical
    paired_rows = []
    for cond in conditions:
        sub_cond = df_predictions[df_predictions["scenario_id"] == cond]
        class_sub = sub_cond[sub_cond["detector"] == "classical"].sort_values("image_id")
        
        for det in ["ai", "hybrid"]:
            det_sub = sub_cond[sub_cond["detector"] == det].sort_values("image_id")
            if len(class_sub) == 0 or len(det_sub) == 0:
                continue

            merged = pd.merge(class_sub, det_sub, on="image_id", suffixes=("_class", f"_{det}"))
            
            # Filter for present images
            merged_present = merged[merged["beacon_present_class"] == True]
            vec_class_tp = ((merged_present["detected_class"] == True) & (merged_present["localization_error_px_class"] <= tolerance_px)).astype(float).values
            vec_det_tp = ((merged_present[f"detected_{det}"] == True) & (merged_present[f"localization_error_px_{det}"] <= tolerance_px)).astype(float).values

            diff_mean, diff_low, diff_high = compute_paired_bootstrap_ci(vec_det_tp, vec_class_tp)

            paired_rows.append({
                "scenario_id": cond,
                "comparison": f"{det}_vs_classical",
                "pd_diff": diff_mean,
                "pd_diff_ci_low": diff_low,
                "pd_diff_ci_high": diff_high
            })

    df_paired = pd.DataFrame(paired_rows)
    return df_summary, df_paired
