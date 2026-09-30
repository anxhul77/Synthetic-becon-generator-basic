import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from .phase_grid import assign_phase_bin, DEFAULT_PHASE_STEPS

def compute_phase_grid_analysis(df_raw: pd.DataFrame, phase_steps: List[float] = None) -> Tuple[pd.DataFrame, Dict[str, Dict[str, np.ndarray]]]:
    """
    Computes phase-dependent statistics and 2D subpixel bias heatmaps for each method.
    Returns (df_phase_analysis, heatmaps_dict).
    """
    if phase_steps is None:
        phase_steps = DEFAULT_PHASE_STEPS

    # Ensure discrete phase assignment
    df = df_raw.copy()
    if "phi_x" in df.columns and "phi_y" in df.columns:
        df["phase_x_bin"] = df["phi_x"].apply(lambda p: assign_phase_bin(p, len(phase_steps)))
        df["phase_y_bin"] = df["phi_y"].apply(lambda p: assign_phase_bin(p, len(phase_steps)))
    else:
        return pd.DataFrame(), {}

    phase_rows = []
    heatmaps_dict = {}

    group_cols = ["method_name", "snr_db", "phase_x_bin", "phase_y_bin"]
    for (method, snr, px, py), group in df.groupby(group_cols):
        total_trials = len(group)
        succ = group[group["success"] == True]
        succ_count = len(succ)
        succ_rate = succ_count / total_trials if total_trials > 0 else 0.0

        if succ_count > 0:
            mean_ex = float(succ["error_x"].mean())
            mean_ey = float(succ["error_y"].mean())
            mean_er = float(succ["radial_error"].mean())
            rmse_r = float(np.sqrt(np.mean(succ["radial_error"].values ** 2)))
            bias_mag = float(np.sqrt(mean_ex ** 2 + mean_ey ** 2))
        else:
            mean_ex, mean_ey, mean_er, rmse_r, bias_mag = np.nan, np.nan, np.nan, np.nan, np.nan

        phase_rows.append({
            "method_name": method,
            "snr_db": float(snr),
            "phi_x": float(px),
            "phi_y": float(py),
            "total_trials": total_trials,
            "success_count": succ_count,
            "success_rate": succ_rate,
            "mean_error_x": mean_ex,
            "mean_error_y": mean_ey,
            "mean_radial_error": mean_er,
            "radial_rmse": rmse_r,
            "bias_magnitude": bias_mag
        })

    df_phase = pd.DataFrame(phase_rows)

    # Build 2D heatmaps matrices (8x8) for primary SNR level (e.g. 15 dB or 30 dB)
    methods = df_phase["method_name"].unique()
    for m in methods:
        sub_m = df_phase[(df_phase["method_name"] == m) & (df_phase["snr_db"] == 15.0)]
        if sub_m.empty:
            sub_m = df_phase[df_phase["method_name"] == m]

        heatmap_x = np.zeros((len(phase_steps), len(phase_steps)), dtype=np.float64)
        heatmap_y = np.zeros((len(phase_steps), len(phase_steps)), dtype=np.float64)
        heatmap_r = np.zeros((len(phase_steps), len(phase_steps)), dtype=np.float64)

        for ix, px in enumerate(phase_steps):
            for iy, py in enumerate(phase_steps):
                match = sub_m[(np.isclose(sub_m["phi_x"], px)) & (np.isclose(sub_m["phi_y"], py))]
                if not match.empty:
                    heatmap_x[iy, ix] = match["mean_error_x"].iloc[0]
                    heatmap_y[iy, ix] = match["mean_error_y"].iloc[0]
                    heatmap_r[iy, ix] = match["mean_radial_error"].iloc[0]

        heatmaps_dict[m] = {
            "heatmap_x": heatmap_x,
            "heatmap_y": heatmap_y,
            "heatmap_r": heatmap_r
        }

    return df_phase, heatmaps_dict
