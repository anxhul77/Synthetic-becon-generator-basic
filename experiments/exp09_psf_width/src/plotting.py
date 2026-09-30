import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def _safe_legend(ax, **kwargs):
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(**kwargs)

def generate_all_experiment_9_plots(
    df_summary: pd.DataFrame,
    df_raw: pd.DataFrame,
    df_phase: pd.DataFrame,
    heatmaps_dict: dict,
    output_dir: str
):
    """
    Generates publication-quality figures for Experiment 9: PSF Width and Localization Accuracy.
    Saves plots to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # Primary baseline slice (9A_primary)
    primary_df = df_summary[df_summary.get("experiment_sub_id", "") == "9A_primary"]
    if primary_df.empty:
        primary_df = df_summary

    methods = primary_df["method_name"].unique() if "method_name" in primary_df.columns else []

    # Figure 1: Radial RMSE vs PSF Width (Primary)
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty:
            ax.plot(m_data["psf_sigma_px"], m_data["radial_rmse"], marker='o', linewidth=2, label=m)
            if "rmse_ci_lower" in m_data.columns and "rmse_ci_upper" in m_data.columns:
                ax.fill_between(m_data["psf_sigma_px"], m_data["rmse_ci_lower"], m_data["rmse_ci_upper"], alpha=0.15)
    ax.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=12)
    ax.set_ylabel("Radial Localization RMSE (pixels)", fontsize=12)
    ax.set_title("Figure 1: Localization RMSE vs PSF Width", fontsize=14, fontweight='bold')
    _safe_legend(ax, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "rmse_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 2: X and Y Localization RMSE
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty and "rmse_x" in m_data.columns and "rmse_y" in m_data.columns:
            ax1.plot(m_data["psf_sigma_px"], m_data["rmse_x"], marker='o', label=m)
            ax2.plot(m_data["psf_sigma_px"], m_data["rmse_y"], marker='s', label=m)
    ax1.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=11)
    ax1.set_ylabel("X-Coordinate RMSE (pixels)", fontsize=11)
    ax1.set_title("X-Coordinate RMSE vs PSF Width", fontsize=12, fontweight='bold')
    _safe_legend(ax1, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=11)
    ax2.set_ylabel("Y-Coordinate RMSE (pixels)", fontsize=11)
    ax2.set_title("Y-Coordinate RMSE vs PSF Width", fontsize=12, fontweight='bold')
    _safe_legend(ax2, fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    fig.suptitle("Figure 2: X and Y Localization RMSE vs PSF Width", fontsize=14, fontweight='bold')
    fig.savefig(os.path.join(output_dir, "x_y_rmse_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, "x_rmse_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, "y_rmse_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 3: Localization Bias vs PSF Width
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty:
            ax1.plot(m_data["psf_sigma_px"], m_data["bias_x"], marker='o', label=m)
            ax2.plot(m_data["psf_sigma_px"], m_data["bias_y"], marker='s', label=m)
    ax1.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=11)
    ax1.set_ylabel("Bias X (pixels)", fontsize=11)
    ax1.set_title("Signed X Bias vs PSF Width", fontsize=12, fontweight='bold')
    ax1.axhline(0, color='black', linestyle=':', alpha=0.5)
    _safe_legend(ax1, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=11)
    ax2.set_ylabel("Bias Y (pixels)", fontsize=11)
    ax2.set_title("Signed Y Bias vs PSF Width", fontsize=12, fontweight='bold')
    ax2.axhline(0, color='black', linestyle=':', alpha=0.5)
    _safe_legend(ax2, fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    fig.suptitle("Figure 3: Localization Bias vs PSF Width", fontsize=14, fontweight='bold')
    fig.savefig(os.path.join(output_dir, "bias_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 4: Localization Success Rate vs PSF Width
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty:
            ax.plot(m_data["psf_sigma_px"], m_data["success_rate"] * 100.0, marker='d', linewidth=2, label=m)
    ax.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=12)
    ax.set_ylabel("Localization Success Rate (%)", fontsize=12)
    ax.set_title("Figure 4: Localization Success Rate vs PSF Width", fontsize=14, fontweight='bold')
    ax.set_ylim(-5, 105)
    _safe_legend(ax, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "success_rate_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 5: Runtime / Latency vs PSF Width
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty and "mean_latency_ms" in m_data.columns:
            ax.plot(m_data["psf_sigma_px"], m_data["mean_latency_ms"], marker='o', linewidth=2, label=f"{m} (Mean)")
            if "p95_latency_ms" in m_data.columns:
                ax.plot(m_data["psf_sigma_px"], m_data["p95_latency_ms"], marker='^', linestyle='--', label=f"{m} (P95)")
    ax.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=12)
    ax.set_ylabel("Localization Latency (ms)", fontsize=12)
    ax.set_title("Figure 5: Runtime vs PSF Width", fontsize=14, fontweight='bold')
    _safe_legend(ax, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "latency_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 6: Angular RMSE vs PSF Width
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
        if not m_data.empty and "angular_rmse_urad" in m_data.columns:
            ax.plot(m_data["psf_sigma_px"], m_data["angular_rmse_urad"], marker='^', linewidth=2, label=m)
    ax.set_xlabel("PSF Width $\\sigma$ (pixels)", fontsize=12)
    ax.set_ylabel("Angular RMSE ($\\mu$rad)", fontsize=12)
    ax.set_title("Figure 6: Angular RMSE vs PSF Width", fontsize=14, fontweight='bold')
    _safe_legend(ax, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "angular_rmse_vs_psf_width.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 7: RMSE vs SNR across PSF widths
    snr_df = df_summary[df_summary.get("experiment_sub_id", "") == "9B_snr"]
    if not snr_df.empty:
        fig, axes = plt.subplots(1, len(methods), figsize=(5 * len(methods), 5), sharey=True)
        if len(methods) == 1:
            axes = [axes]
        sigmas = sorted(snr_df["psf_sigma_px"].unique())
        if hasattr(plt, "colormaps"):
            cmap = plt.colormaps["plasma"].resampled(len(sigmas))
        else:
            cmap = plt.cm.get_cmap("plasma", len(sigmas))

        for idx, m in enumerate(methods):
            ax = axes[idx]
            m_snr = snr_df[snr_df["method_name"] == m]
            for s_idx, sig in enumerate(sigmas):
                sig_data = m_snr[m_snr["psf_sigma_px"] == sig].sort_values("snr_db")
                if not sig_data.empty:
                    ax.plot(sig_data["snr_db"], sig_data["radial_rmse"], marker='o', color=cmap(s_idx), label=f"$\\sigma$={sig}")
            ax.set_xlabel("Configured SNR (dB)", fontsize=11)
            if idx == 0:
                ax.set_ylabel("Radial RMSE (px)", fontsize=11)
            ax.set_title(f"{m}", fontsize=12, fontweight='bold')
            _safe_legend(ax, fontsize=8, loc='upper right')
            ax.grid(True, linestyle='--', alpha=0.7)
        fig.suptitle("Figure 7: Localization RMSE vs SNR across PSF Widths", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 8: RMSE vs Background
    bg_df = df_summary[df_summary.get("experiment_sub_id", "") == "9C_background"]
    if not bg_df.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        for m in methods:
            m_bg = bg_df[bg_df["method_name"] == m].groupby("background_level")["radial_rmse"].mean().reset_index()
            ax.plot(m_bg["background_level"], m_bg["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("Background Level (DN)", fontsize=12)
        ax.set_ylabel("Radial Localization RMSE (pixels)", fontsize=12)
        ax.set_title("Figure 8: Localization RMSE vs Background Level", fontsize=14, fontweight='bold')
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "rmse_vs_background.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 9: Subpixel Phase Error Maps
    if heatmaps_dict:
        n_maps = len(heatmaps_dict)
        fig, axes = plt.subplots(1, n_maps, figsize=(4 * n_maps, 4))
        if n_maps == 1:
            axes = [axes]
        for idx, (key_name, hm_data) in enumerate(heatmaps_dict.items()):
            im = axes[idx].imshow(hm_data["heatmap_r"], extent=[0, 1, 0, 1], origin='lower', cmap='viridis')
            axes[idx].set_title(key_name, fontsize=10, fontweight='bold')
            axes[idx].set_xlabel("$\\phi_x$", fontsize=10)
            if idx == 0:
                axes[idx].set_ylabel("$\\phi_y$", fontsize=10)
            fig.colorbar(im, ax=axes[idx], fraction=0.046, pad=0.04)
        fig.suptitle("Figure 9: Subpixel Phase Error Heatmaps over Fractional Phase Grid ($\\phi_x, \\phi_y$)", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "phase_error_heatmaps.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 10: Localization Error Distributions
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df_raw.empty and "radial_error_px" in df_raw.columns:
        valid_raw = df_raw[df_raw["success"] == True]
        data_to_plot = []
        labels = []
        for sig in sorted(valid_raw["psf_sigma_px"].unique()):
            for m in methods:
                errs = valid_raw[(valid_raw["psf_sigma_px"] == sig) & (valid_raw["method_name"] == m)]["radial_error_px"].dropna().values
                if len(errs) > 0:
                    data_to_plot.append(errs)
                    labels.append(f"$\\sigma$={sig}\n{m[:5]}")
        if len(data_to_plot) > 0:
            try:
                ax.boxplot(data_to_plot, tick_labels=labels, showfliers=False)
            except TypeError:
                ax.boxplot(data_to_plot, labels=labels, showfliers=False)
            ax.set_ylabel("Radial Error (pixels)", fontsize=12)
            ax.set_title("Figure 10: Localization Error Distributions by PSF Width & Method", fontsize=14, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.7)
            fig.savefig(os.path.join(output_dir, "error_distributions.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 11: Fixed Energy vs Fixed Amplitude Comparison
    energy_df = df_summary[df_summary.get("experiment_sub_id", "") == "9E_fixed_energy"]
    if not energy_df.empty:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        for m in methods:
            m_prim = primary_df[primary_df["method_name"] == m].sort_values("psf_sigma_px")
            m_eng = energy_df[energy_df["method_name"] == m].sort_values("psf_sigma_px")
            if not m_prim.empty:
                ax1.plot(m_prim["psf_sigma_px"], m_prim["radial_rmse"], marker='o', label=f"{m} (Fixed Peak A)")
            if not m_eng.empty:
                ax2.plot(m_eng["psf_sigma_px"], m_eng["radial_rmse"], marker='s', linestyle='--', label=f"{m} (Fixed Energy)")
        ax1.set_xlabel("PSF Width $\\sigma$ (px)", fontsize=11)
        ax1.set_ylabel("Radial RMSE (px)", fontsize=11)
        ax1.set_title("Fixed Peak Amplitude ($A=150$)", fontsize=12, fontweight='bold')
        _safe_legend(ax1, fontsize=9)
        ax1.grid(True, linestyle='--', alpha=0.7)

        ax2.set_xlabel("PSF Width $\\sigma$ (px)", fontsize=11)
        ax2.set_ylabel("Radial RMSE (px)", fontsize=11)
        ax2.set_title("Fixed Integrated Signal Energy ($E=const$)", fontsize=12, fontweight='bold')
        _safe_legend(ax2, fontsize=9)
        ax2.grid(True, linestyle='--', alpha=0.7)

        fig.suptitle("Figure 11: Fixed Peak Amplitude vs Fixed Integrated Energy Comparison", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "fixed_energy_vs_amplitude.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 12: ROI-Size Sensitivity Across PSF Widths
    roi_df = df_summary[df_summary.get("experiment_sub_id", "") == "9F_roi_sensitivity"]
    if not roi_df.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        for m in methods:
            m_roi = roi_df[roi_df["method_name"] == m].groupby("roi_size")["radial_rmse"].mean().reset_index()
            ax.plot(m_roi["roi_size"], m_roi["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("ROI Size (pixels)", fontsize=12)
        ax.set_ylabel("Radial Localization RMSE (pixels)", fontsize=12)
        ax.set_title("Figure 12: ROI Size Sensitivity across Estimators", fontsize=14, fontweight='bold')
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "roi_size_sensitivity.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)
