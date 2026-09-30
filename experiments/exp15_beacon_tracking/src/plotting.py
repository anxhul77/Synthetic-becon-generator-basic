import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def set_style():
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 15,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11,
        'figure.titlesize': 16,
        'figure.dpi': 300
    })

def plot_2d_trajectories(df_seq: pd.DataFrame, output_path: str):
    """Figure 1: 2D Trajectory overlay (Ground Truth vs Tracker Estimates across motion models)."""
    set_style()
    motion_types = df_seq["motion_type"].unique()
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for idx, m_type in enumerate(motion_types[:6]):
        ax = axes[idx]
        sub = df_seq[(df_seq["motion_type"] == m_type) & (df_seq["method"] == "Gaussian Fitting")]
        if sub.empty:
            continue

        ax.plot(sub["x_gt"], sub["y_gt"], "k-", linewidth=2.5, label="Ground Truth")
        ax.plot(sub["x_est"], sub["y_est"], "r--", linewidth=1.5, label="Tracker Estimate")

        # Highlight occlusions if present
        occluded = sub[sub["is_occluded_gt"] == True]
        if not occluded.empty:
            ax.scatter(occluded["x_gt"], occluded["y_gt"], color="orange", s=30, zorder=5, label="Occluded (Cloud Fade)")

        ax.set_title(f"Trajectory: {m_type.replace('_', ' ').title()}")
        ax.set_xlabel("x Position [px]")
        ax.set_ylabel("y Position [px]")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

    # Hide unused axes
    for j in range(len(motion_types), len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_temporal_position_error(df_seq: pd.DataFrame, output_path: str):
    """Figure 2: Temporal Position Error e(t) over sequence frames."""
    set_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    for m_type in df_seq["motion_type"].unique():
        sub = df_seq[(df_seq["motion_type"] == m_type) & (df_seq["method"] == "Gaussian Fitting")]
        if sub.empty:
            continue
        ax.plot(sub["frame_idx"], sub["pos_error_px"], label=f"{m_type.replace('_', ' ').title()}", linewidth=1.8)

    ax.set_title("Experiment 15: Temporal Position Error e(t) Across Motion Models")
    ax.set_xlabel("Frame Index t")
    ax.set_ylabel("Position Error e(t) [px]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_angular_pointing_error(df_seq: pd.DataFrame, output_path: str):
    """Figure 3: Temporal Angular Pointing Error e_theta(t) in microradians."""
    set_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    for m_type in df_seq["motion_type"].unique():
        sub = df_seq[(df_seq["motion_type"] == m_type) & (df_seq["method"] == "Gaussian Fitting")]
        if sub.empty:
            continue
        ax.plot(sub["frame_idx"], sub["angular_error_urad"], label=f"{m_type.replace('_', ' ').title()}", linewidth=1.8)

    ax.set_title("Experiment 15: Temporal Angular Pointing Error e_θ(t) [μrad]")
    ax.set_xlabel("Frame Index t")
    ax.set_ylabel("Pointing Angle Error e_θ(t) [μrad]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_occlusion_reacquisition(df_seq: pd.DataFrame, output_path: str):
    """Figure 4: Tracking Loss & Reacquisition Time T_reacquire under Occlusion Fade."""
    set_style()
    sub = df_seq[(df_seq["motion_type"] == "occlusion_fade") & (df_seq["method"] == "Gaussian Fitting")]
    if sub.empty:
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax1.plot(sub["frame_idx"], sub["pos_error_px"], "b-", linewidth=2, label="Position Error e(t) [px]")
    ax1.axvspan(35, 55, color="red", alpha=0.2, label="Signal Occlusion Window")
    ax1.set_ylabel("Position Error [px]")
    ax1.set_title("Experiment 15: Beacon Loss & Reacquisition Time Demo")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # State timeline
    states = sub["track_state"].values
    state_codes = [1 if s == "TRACKING" else (0.5 if s == "REACQUIRING" else 0) for s in states]
    ax2.step(sub["frame_idx"], state_codes, "g-", where="post", linewidth=2.5, label="Tracker State Machine")
    ax2.axvspan(35, 55, color="red", alpha=0.2)
    ax2.set_yticks([0, 0.5, 1])
    ax2.set_yticklabels(["LOST", "REACQUIRING", "TRACKING"])
    ax2.set_xlabel("Frame Index t")
    ax2.set_ylabel("Tracker State")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_tracking_summary_bars(df_summary: pd.DataFrame, output_path: str):
    """Figure 5: Summary RMSE Position Error and Track Maintenance Ratio by Motion Type."""
    set_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    sub = df_summary[df_summary["method"] == "Gaussian Fitting"]
    motion_names = [m.replace("_", " ").title() for m in sub["motion_type"]]
    rmse_vals = sub["rmse_pos_error_px"]
    p_track_vals = sub["track_ratio"] * 100.0

    ax1.bar(motion_names, rmse_vals, color="skyblue", edgecolor="navy", alpha=0.85)
    ax1.set_title("RMSE Position Error across Motion Models")
    ax1.set_ylabel("RMSE Position Error [px]")
    ax1.tick_params(axis='x', rotation=25)
    ax1.grid(True, alpha=0.3)

    ax2.bar(motion_names, p_track_vals, color="lightgreen", edgecolor="darkgreen", alpha=0.85)
    ax2.set_title("Track Maintenance Ratio (P_track %)")
    ax2.set_ylabel("Tracked Frames [%]")
    ax2.set_ylim(0, 105)
    ax2.tick_params(axis='x', rotation=25)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_processing_latency(df_seq: pd.DataFrame, output_path: str):
    """Figure 6: Frame Processing Latency T_processing per frame."""
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    methods = df_seq["method"].unique()
    latency_data = [df_seq[df_seq["method"] == m]["latency_ms"].dropna() for m in methods]

    try:
        ax.boxplot(latency_data, tick_labels=methods, patch_artist=True)
    except TypeError:
        ax.boxplot(latency_data, labels=methods, patch_artist=True)

    ax.set_title("Experiment 15: Tracker Frame Processing Latency T_processing [ms]")
    ax.set_ylabel("Latency [ms/frame]")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def generate_all_experiment_15_plots(df_seq: pd.DataFrame, df_summary: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plot_2d_trajectories(df_seq, os.path.join(output_dir, "2d_trajectories.png"))
    plot_temporal_position_error(df_seq, os.path.join(output_dir, "temporal_position_error.png"))
    plot_angular_pointing_error(df_seq, os.path.join(output_dir, "temporal_angular_error.png"))
    plot_occlusion_reacquisition(df_seq, os.path.join(output_dir, "occlusion_reacquisition.png"))
    plot_tracking_summary_bars(df_summary, os.path.join(output_dir, "tracking_summary_bars.png"))
    plot_processing_latency(df_seq, os.path.join(output_dir, "processing_latency.png"))
