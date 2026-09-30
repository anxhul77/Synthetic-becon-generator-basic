import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

def generate_all_experiment_11_plots(
    df_summary: pd.DataFrame,
    df_raw: pd.DataFrame,
    df_paired: pd.DataFrame,
    df_interaction: pd.DataFrame,
    df_factorial: pd.DataFrame,
    output_dir: str
) -> None:
    """
    Generates 10 publication-quality figures for Experiment 11 using matplotlib.
    """
    os.makedirs(output_dir, exist_ok=True)

    method_col = "method_name" if "method_name" in df_summary.columns else "method"

    _plot_psf_snr_rmse_heatmaps(df_summary, output_dir, method_col)
    _plot_psf_background_rmse_heatmaps(df_summary, output_dir, method_col)
    _plot_psf_snr_interaction(df_summary, output_dir, method_col)
    _plot_psf_background_interaction(df_summary, output_dir, method_col)
    _plot_snr_background_interaction(df_summary, output_dir, method_col)
    _plot_localization_bias(df_summary, output_dir, method_col)
    _plot_success_rate_heatmaps(df_summary, output_dir, method_col)
    _plot_runtime_comparison(df_summary, output_dir, method_col)
    _plot_angular_rmse_heatmaps(df_summary, output_dir, method_col)
    _plot_error_distributions(df_raw, output_dir, method_col)


def _plot_heatmap_mat(ax, pivot_df, title, xlabel, ylabel, cmap_name="YlOrRd", fmt=".3f", vmin=None, vmax=None):
    data = pivot_df.values
    im = ax.imshow(data, cmap=cmap_name, aspect="auto", vmin=vmin, vmax=vmax)
    ax.set_xticks(np.arange(len(pivot_df.columns)))
    ax.set_yticks(np.arange(len(pivot_df.index)))
    ax.set_xticklabels([f"{c:g}" for c in pivot_df.columns])
    ax.set_yticklabels([f"{r:g}" for r in pivot_df.index])
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Annotate values
    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            val = data[r, c]
            if not np.isnan(val):
                text_str = f"{val:{fmt[1:]}}"
                ax.text(c, r, text_str, ha="center", va="center", color="black", fontsize=8)
    return im


def _plot_psf_snr_rmse_heatmaps(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    bg_levels = sorted(df_summary["background_level"].unique())
    methods = sorted(df_summary[method_col].unique())

    fig, axes = plt.subplots(len(bg_levels), len(methods),
                             figsize=(4 * len(methods), 3.2 * len(bg_levels)),
                             squeeze=False)

    for i, bg in enumerate(bg_levels):
        for j, method in enumerate(methods):
            ax = axes[i, j]
            sub = df_summary[(df_summary["background_level"] == bg) & (df_summary[method_col] == method)]
            if not sub.empty:
                pivot = sub.pivot_table(index="psf_sigma_px", columns="snr_db", values="radial_rmse", aggfunc="mean")
                _plot_heatmap_mat(ax, pivot, f"{method}\nB = {bg:g} DN", "SNR (dB)", "PSF σ (px)", cmap_name="YlOrRd")

    plt.suptitle("Fig 1: Localization RMSE (px) across PSF Width and SNR", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "psf_snr_rmse_heatmaps.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_psf_background_rmse_heatmaps(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    snr_levels = sorted(df_summary["snr_db"].unique())
    methods = sorted(df_summary[method_col].unique())

    fig, axes = plt.subplots(len(snr_levels), len(methods),
                             figsize=(4 * len(methods), 3.2 * len(snr_levels)),
                             squeeze=False)

    for i, snr in enumerate(snr_levels):
        for j, method in enumerate(methods):
            ax = axes[i, j]
            sub = df_summary[(df_summary["snr_db"] == snr) & (df_summary[method_col] == method)]
            if not sub.empty:
                pivot = sub.pivot_table(index="psf_sigma_px", columns="background_level", values="radial_rmse", aggfunc="mean")
                _plot_heatmap_mat(ax, pivot, f"{method}\nSNR = {snr:g} dB", "Background (DN)", "PSF σ (px)", cmap_name="YlOrRd")

    plt.suptitle("Fig 2: Localization RMSE (px) across PSF Width and Background Level", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "psf_background_rmse_heatmaps.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_psf_snr_interaction(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 4), sharey=True)
    if len(methods) == 1:
        axes = [axes]

    target_bg = 50.0 if 50.0 in df_summary["background_level"].values else df_summary["background_level"].values[0]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[(df_summary["background_level"] == target_bg) & (df_summary[method_col] == method)]
        for idx, sig in enumerate(sorted(sub["psf_sigma_px"].unique())):
            s_sig = sub[sub["psf_sigma_px"] == sig].sort_values("snr_db")
            ax.plot(s_sig["snr_db"], s_sig["radial_rmse"], marker="o", linewidth=2, color=colors[idx % len(colors)], label=f"σ = {sig:g} px")

        ax.set_title(f"{method}\n(B = {target_bg:g} DN)", fontsize=11, fontweight="bold")
        ax.set_xlabel("SNR (dB)")
        ax.set_ylabel("Localization RMSE (px)")
        ax.legend(title="PSF Width")
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Fig 3: PSF Width × SNR Interaction Curves", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "psf_snr_interaction.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_psf_background_interaction(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 4), sharey=True)
    if len(methods) == 1:
        axes = [axes]

    target_snr = 15.0 if 15.0 in df_summary["snr_db"].values else df_summary["snr_db"].values[0]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[(df_summary["snr_db"] == target_snr) & (df_summary[method_col] == method)]
        for idx, sig in enumerate(sorted(sub["psf_sigma_px"].unique())):
            s_sig = sub[sub["psf_sigma_px"] == sig].sort_values("background_level")
            ax.plot(s_sig["background_level"], s_sig["radial_rmse"], marker="s", linewidth=2, color=colors[idx % len(colors)], label=f"σ = {sig:g} px")

        ax.set_title(f"{method}\n(SNR = {target_snr:g} dB)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Background Level (DN)")
        ax.set_ylabel("Localization RMSE (px)")
        ax.legend(title="PSF Width")
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Fig 4: PSF Width × Background Interaction Curves", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "psf_background_interaction.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_snr_background_interaction(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 4), sharey=True)
    if len(methods) == 1:
        axes = [axes]

    target_sigma = 2.0 if 2.0 in df_summary["psf_sigma_px"].values else df_summary["psf_sigma_px"].values[0]
    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#e7298a"]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[(df_summary["psf_sigma_px"] == target_sigma) & (df_summary[method_col] == method)]
        for idx, bg in enumerate(sorted(sub["background_level"].unique())):
            s_bg = sub[sub["background_level"] == bg].sort_values("snr_db")
            ax.plot(s_bg["snr_db"], s_bg["radial_rmse"], marker="^", linewidth=2, color=colors[idx % len(colors)], label=f"B = {bg:g} DN")

        ax.set_title(f"{method}\n(PSF σ = {target_sigma:g} px)", fontsize=11, fontweight="bold")
        ax.set_xlabel("SNR (dB)")
        ax.set_ylabel("Localization RMSE (px)")
        ax.legend(title="Background")
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Fig 5: SNR × Background Interaction Curves", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "snr_background_interaction.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_localization_bias(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary[(df_summary["snr_db"] == 15.0) & (df_summary["background_level"] == 50.0)]
    if sub.empty:
        sub = df_summary

    sigmas = sorted(sub["psf_sigma_px"].unique())
    methods = sorted(sub[method_col].unique())
    x = np.arange(len(sigmas))
    width = 0.8 / len(methods)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for j, method in enumerate(methods):
        biases = []
        for sig in sigmas:
            row = sub[(sub["psf_sigma_px"] == sig) & (sub[method_col] == method)]
            if not row.empty:
                if "bias_magnitude" in row.columns:
                    b_val = float(row["bias_magnitude"].values[0])
                elif "bias_2d" in row.columns:
                    b_val = float(row["bias_2d"].values[0])
                elif "bias_x" in row.columns and "bias_y" in row.columns:
                    bx = float(row["bias_x"].values[0])
                    by = float(row["bias_y"].values[0])
                    b_val = float(np.sqrt(bx**2 + by**2))
                else:
                    b_val = 0.0
            else:
                b_val = 0.0
            biases.append(b_val)
        ax.bar(x + j * width - 0.4 + width / 2, biases, width, label=method, color=colors[j % len(colors)])

    ax.set_xticks(x)
    ax.set_xticklabels([f"σ = {s:g}" for s in sigmas], fontweight="bold")
    ax.set_title("Fig 6: 2D Systematic Localization Bias across PSF Width", fontsize=12, fontweight="bold")
    ax.set_xlabel("PSF Standard Deviation σ (px)")
    ax.set_ylabel("2D Systematic Bias (px)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "localization_bias.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_success_rate_heatmaps(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(4.5 * len(methods), 3.8))
    if len(methods) == 1:
        axes = [axes]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[df_summary[method_col] == method]
        pivot = sub.groupby(["psf_sigma_px", "snr_db"])["success_rate"].mean().unstack()
        _plot_heatmap_mat(ax, pivot, f"{method}\nSuccess Rate P_success", "SNR (dB)", "PSF σ (px)", cmap_name="YlGn", fmt=".1%", vmin=0.8, vmax=1.0)

    plt.suptitle("Fig 7: Estimator Success Rate across PSF Width and SNR", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "success_rate_heatmaps.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_runtime_comparison(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))

    sub = df_summary.groupby(method_col).agg({
        "mean_latency_ms": "mean",
        "median_latency_ms": "mean",
        "p95_latency_ms": "mean"
    }).reset_index()

    x = np.arange(len(sub[method_col]))
    width = 0.25

    ax.bar(x - width, sub["mean_latency_ms"], width, label="Mean Latency (ms)", color="#2b5c8f")
    ax.bar(x, sub["median_latency_ms"], width, label="Median Latency (ms)", color="#4682b4")
    ax.bar(x + width, sub["p95_latency_ms"], width, label="95th Percentile (ms)", color="#d95f02")

    ax.set_xticks(x)
    ax.set_xticklabels(sub[method_col], fontweight="bold")
    ax.set_ylabel("Processing Latency (ms / ROI)")
    ax.set_title("Fig 8: Processing Latency Comparison Across Estimators", fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "runtime_comparison.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_angular_rmse_heatmaps(df_summary: pd.DataFrame, output_dir: str, method_col: str):
    methods = sorted(df_summary[method_col].unique())
    fig, axes = plt.subplots(1, len(methods), figsize=(4.5 * len(methods), 3.8))
    if len(methods) == 1:
        axes = [axes]

    for j, method in enumerate(methods):
        ax = axes[j]
        sub = df_summary[df_summary[method_col] == method]
        pivot = sub.groupby(["psf_sigma_px", "snr_db"])["angular_rmse_urad"].mean().unstack()
        _plot_heatmap_mat(ax, pivot, f"{method}\nAngular RMSE (μrad)", "SNR (dB)", "PSF σ (px)", cmap_name="Purples", fmt=".1f")

    plt.suptitle("Fig 9: Angular Localization RMSE (μrad) across PSF Width and SNR", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "angular_rmse_heatmaps.png"), dpi=300, bbox_inches="tight")
    plt.close()


def _plot_error_distributions(df_raw: pd.DataFrame, output_dir: str, method_col: str):
    fig, ax = plt.subplots(figsize=(8.5, 4.5))

    sub = df_raw[(df_raw["snr_db"] == 15.0) & (df_raw["background_level"] == 50.0) & (df_raw["success"] == True)]
    if sub.empty:
        sub = df_raw[df_raw["success"] == True]

    sigmas = sorted(sub["psf_sigma_px"].unique())
    methods = sorted(sub[method_col].unique())

    data_to_plot = []
    labels = []
    for sig in sigmas:
        for m in methods:
            errs = sub[(sub["psf_sigma_px"] == sig) & (sub[method_col] == m)]["radial_error_px"].values
            data_to_plot.append(errs if len(errs) > 0 else [0.0])
            labels.append(f"σ={sig:g}\n{m[:5]}")

    if data_to_plot:
        try:
            ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True, boxprops=dict(facecolor="#8da0cb", color="#386cb0"))
        except TypeError:
            ax.boxplot(data_to_plot, patch_artist=True, boxprops=dict(facecolor="#8da0cb", color="#386cb0"))
            ax.set_xticks(np.arange(1, len(labels) + 1))
            ax.set_xticklabels(labels)

    ax.set_title("Fig 10: Subpixel Radial Error Distributions across PSF Width (SNR = 15 dB)", fontsize=12, fontweight="bold")
    ax.set_xlabel("PSF Width & Estimator")
    ax.set_ylabel("Radial Error (px)")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "error_distributions.png"), dpi=300, bbox_inches="tight")
    plt.close()
