import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

def generate_all_experiment_14_plots(
    df_summary: pd.DataFrame,
    df_raw: pd.DataFrame,
    df_paired: pd.DataFrame,
    df_fov_summary: pd.DataFrame,
    output_dir: str
) -> None:
    """
    Generates 10 publication-quality figures for Experiment 14.
    """
    os.makedirs(output_dir, exist_ok=True)

    method_col = "method_name" if "method_name" in df_summary.columns else "method"

    _plot_angular_rmse_vs_focal_length(df_summary, output_dir, method_col)
    _plot_pixel_vs_angular_error_comparison(df_summary, output_dir, method_col)
    _plot_fov_vs_angular_precision(df_summary, output_dir, method_col)
    _plot_off_axis_angular_error(df_summary, output_dir, method_col)
    _plot_angular_error_heatmaps(df_summary, output_dir, method_col)
    _plot_angular_bias_analysis(df_summary, output_dir, method_col)
    _plot_angular_error_distributions(df_raw, output_dir, method_col)
    _plot_angular_precision_gain(df_summary, output_dir, method_col)
    _plot_estimator_angular_comparison(df_summary, output_dir, method_col)
    _plot_runtime_vs_focal_length(df_summary, output_dir, method_col)


def _plot_heatmap_mat(ax, pivot_df, title, xlabel, ylabel, cmap_name="Purples", fmt=".1f"):
    data = pivot_df.values
    im = ax.imshow(data, cmap=cmap_name, aspect="auto")
    ax.set_xticks(np.arange(len(pivot_df.columns)))
    ax.set_yticks(np.arange(len(pivot_df.index)))
    ax.set_xticklabels([f"{c:g}" for c in pivot_df.columns])
    ax.set_yticklabels([f"{r:g}" for r in pivot_df.index])
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            val = data[r, c]
            if not np.isnan(val):
                ax.text(c, r, f"{val:{fmt[1:]}}", ha="center", va="center", color="black", fontsize=8)
    return im


def _plot_angular_rmse_vs_focal_length(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 4), sharey=True)
    if len(methods) == 1:
        axes = [axes]

    colors = ["#d95f02", "#7570b3", "#e7298a", "#1b9e77", "#e6ab02"]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[df_summary[method_col] == method]
        for idx, snr in enumerate(sorted(sub["snr_db"].unique())):
            s_snr = sub[sub["snr_db"] == snr].sort_values("focal_length_px")
            ax.plot(s_snr["focal_length_px"], s_snr["angular_rmse_urad"], marker="o", linewidth=2,
                    color=colors[idx % len(colors)], label=f"SNR = {snr:g} dB")

        ax.set_title(f"{method}\nPointing Error vs Focal Length", fontsize=11, fontweight="bold")
        ax.set_xlabel("Camera Focal Length fx (px)")
        ax.set_ylabel("Angular Pointing RMSE (μrad)")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Fig 1: Angular Pointing RMSE (μrad) vs Camera Focal Length", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_rmse_vs_focal_length.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_pixel_vs_angular_error_comparison(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax1 = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary[method_col] == "Gaussian Fitting") & (df_summary["snr_db"] == 15.0)].sort_values("focal_length_px")

    f_vals = sub["focal_length_px"].values
    px_rmse = sub["radial_rmse"].values
    ang_rmse = sub["angular_rmse_urad"].values

    color1 = "#1f77b4"
    ax1.plot(f_vals, px_rmse, color=color1, marker="s", linewidth=2, label="Pixel Error (px)")
    ax1.set_xlabel("Camera Focal Length fx (px)", fontweight="bold")
    ax1.set_ylabel("Pixel Radial Error (px)", color=color1, fontweight="bold")
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xscale("log")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    color2 = "#d95f02"
    ax2.plot(f_vals, ang_rmse, color=color2, marker="o", linewidth=2, linestyle="--", label="Angular Error (μrad)")
    ax2.set_ylabel("Pointing Angle Error e_theta (μrad)", color=color2, fontweight="bold")
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_yscale("log")

    plt.title("Fig 2: Dual-Axis Comparison — Pixel Error vs Physical Pointing Error", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pixel_vs_angular_error_comparison.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_fov_vs_angular_precision(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary["snr_db"] == 15.0)].sort_values("fov_x_deg")
    methods = sorted(sub[method_col].unique())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for j, method in enumerate(methods):
        s_m = sub[sub[method_col] == method]
        ax.plot(s_m["fov_x_deg"], s_m["angular_rmse_urad"], marker="^", linewidth=2, color=colors[j % len(colors)], label=method)

    ax.set_xlabel("Camera Horizontal FOV_x (degrees)", fontweight="bold")
    ax.set_ylabel("Angular Pointing RMSE (μrad)", fontweight="bold")
    ax.set_title("Fig 3: Pointing Precision vs Camera Field-Of-View (FOV)", fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fov_vs_angular_precision.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_off_axis_angular_error(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    sub = df_summary[df_summary["experiment_sub_id"] == "14B_off_axis"]
    if sub.empty:
        sub = df_summary

    fig, ax = plt.subplots(figsize=(8, 4.5))
    methods = sorted(sub[method_col].unique())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for j, method in enumerate(methods):
        s_m = sub[sub[method_col] == method].sort_values("radial_offset_px")
        if not s_m.empty:
            ax.plot(s_m["radial_offset_px"], s_m["angular_rmse_urad"], marker="d", linewidth=2, color=colors[j % len(colors)], label=method)

    ax.set_xlabel("Sensor Radial Distance from Center (px)", fontweight="bold")
    ax.set_ylabel("Angular Pointing RMSE (μrad)", fontweight="bold")
    ax.set_title("Fig 4: Off-Axis Pointing Precision vs Sensor Radial Field Offset", fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "off_axis_angular_error.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_angular_error_heatmaps(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(4.5 * len(methods), 3.8))
    if len(methods) == 1:
        axes = [axes]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[df_summary[method_col] == method]
        pivot = sub.pivot_table(index="focal_length_px", columns="snr_db", values="angular_rmse_urad", aggfunc="mean")
        _plot_heatmap_mat(ax, pivot, f"{method}\nAngular RMSE (μrad)", "SNR (dB)", "Focal Length fx (px)", cmap_name="Purples", fmt=".1f")

    plt.suptitle("Fig 5: Angular Pointing RMSE (μrad) across Focal Length and SNR", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_error_heatmaps.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_angular_bias_analysis(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary["snr_db"] == 15.0) & (df_summary[method_col] == "Gaussian Fitting")].sort_values("focal_length_px")
    if sub.empty:
        sub = df_summary

    f_vals = sub["focal_length_px"].values
    bias_mag = sub["bias_magnitude"].values * (1e6 / f_vals) if "bias_magnitude" in sub.columns else np.zeros_like(f_vals)

    ax.plot(f_vals, bias_mag, marker="o", color="#e7298a", linewidth=2, label="2D Systematic Angular Bias (μrad)")
    ax.set_xlabel("Camera Focal Length fx (px)", fontweight="bold")
    ax.set_ylabel("Systematic Angular Bias (μrad)", fontweight="bold")
    ax.set_title("Fig 6: Systematic Angular Pointing Bias across Focal Length", fontsize=12, fontweight="bold")
    ax.set_xscale("log")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_bias_analysis.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_angular_error_distributions(df_raw: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8.5, 4.5))

    sub = df_raw[(df_raw["snr_db"] == 15.0) & (df_raw["success"] == True)]
    if sub.empty:
        sub = df_raw[df_raw["success"] == True]

    f_levels = sorted(sub["focal_length_px"].unique())
    data_to_plot = []
    labels = []

    for f in f_levels:
        errs = sub[(sub["focal_length_px"] == f) & (sub[method_col] == "Gaussian Fitting")]["angular_error_urad"].values
        data_to_plot.append(errs if len(errs) > 0 else [0.0])
        labels.append(f"f={f:g}px")

    if data_to_plot:
        try:
            ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True, boxprops=dict(facecolor="#7570b3", color="#386cb0"))
        except TypeError:
            ax.boxplot(data_to_plot, patch_artist=True, boxprops=dict(facecolor="#7570b3", color="#386cb0"))
            ax.set_xticks(np.arange(1, len(labels) + 1))
            ax.set_xticklabels(labels)

    ax.set_yscale("log")
    ax.set_title("Fig 7: Angular Pointing Error Distributions (μrad) across Focal Length (SNR = 15 dB)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Camera Focal Length fx (px)")
    ax.set_ylabel("Angular Pointing Error e_theta (μrad)")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_error_distributions.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_angular_precision_gain(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary["snr_db"] == 15.0) & (df_summary[method_col] == "Gaussian Fitting")].sort_values("focal_length_px")
    if not sub.empty:
        base_ang = sub[sub["focal_length_px"] == sub["focal_length_px"].min()]["angular_rmse_urad"].values[0]
        reduction_pct = (1.0 - sub["angular_rmse_urad"].values / base_ang) * 100.0
        ax.plot(sub["focal_length_px"].values, reduction_pct, marker="s", color="#2ca02c", linewidth=2)

    ax.set_xlabel("Camera Focal Length fx (px)", fontweight="bold")
    ax.set_ylabel("Pointing Precision Gain (%)", fontweight="bold")
    ax.set_title("Fig 8: Pointing Error Reduction Gain vs Baseline Broad FOV (fx = 500 px)", fontsize=12, fontweight="bold")
    ax.set_xscale("log")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_precision_gain.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_estimator_angular_comparison(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary["snr_db"] == 15.0) & (df_summary["focal_length_px"] == 2000.0)]
    if sub.empty:
        sub = df_summary

    methods = sorted(sub[method_col].unique())
    rmse_vals = [sub[sub[method_col] == m]["angular_rmse_urad"].values[0] if not sub[sub[method_col] == m].empty else 0.0 for m in methods]

    ax.bar(methods, rmse_vals, color=["#1f77b4", "#ff7f0e", "#2ca02c"], width=0.5)
    ax.set_ylabel("Angular Pointing RMSE (μrad)", fontweight="bold")
    ax.set_title("Fig 9: Estimator Comparison in Physical Pointing Space (fx = 2000 px, SNR = 15 dB)", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "estimator_angular_comparison.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_runtime_vs_focal_length(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary.groupby(method_col)["mean_latency_ms"].mean().reset_index()
    ax.bar(sub[method_col], sub["mean_latency_ms"], color="#4682b4", width=0.5)

    ax.set_ylabel("Mean Processing Latency (ms / ROI)", fontweight="bold")
    ax.set_title("Fig 10: Processing Latency Invariance Across Optical Configurations", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "runtime_vs_focal_length.png"), dpi=300, bbox_inches="tight")
    plt.close()
