import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .phase_grid import DEFAULT_PHASE_STEPS

def generate_all_experiment_8_plots(
    df_summary: pd.DataFrame,
    df_raw: pd.DataFrame,
    df_phase: pd.DataFrame,
    heatmaps_dict: dict,
    output_dir: str
):
    """
    Generates Figures 1-12 for Experiment 8 with publication-quality styling.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    f1_df = df_summary[df_summary.get("experiment_sub_id", "") == "8A_random_snr"]
    if f1_df.empty and "snr_db" in df_summary.columns:
        f1_df = df_summary

    methods = f1_df["method_name"].unique() if "method_name" in f1_df.columns else []

    # Figure 1: Radial RMSE vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["radial_rmse"], marker='o', linewidth=2, label=m)
            if "rmse_ci_lower" in m_data.columns and "rmse_ci_upper" in m_data.columns:
                ax.fill_between(m_data["snr_db"], m_data["rmse_ci_lower"], m_data["rmse_ci_upper"], alpha=0.15)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
    ax.set_title("Figure 1: Radial Pixel RMSE vs Configured SNR", fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig01_radial_rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 2: X and Y RMSE vs SNR
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty and "rmse_x" in m_data.columns and "rmse_y" in m_data.columns:
            ax1.plot(m_data["snr_db"], m_data["rmse_x"], marker='o', label=m)
            ax2.plot(m_data["snr_db"], m_data["rmse_y"], marker='s', label=m)
    ax1.set_xlabel("SNR (dB)", fontsize=11)
    ax1.set_ylabel("X-Coordinate RMSE (px)", fontsize=11)
    ax1.set_title("X-Coordinate RMSE vs SNR", fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.set_xlabel("SNR (dB)", fontsize=11)
    ax2.set_ylabel("Y-Coordinate RMSE (px)", fontsize=11)
    ax2.set_title("Y-Coordinate RMSE vs SNR", fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    fig.suptitle("Figure 2: Separate X and Y Coordinate RMSE vs SNR", fontsize=14, fontweight='bold')
    fig.savefig(os.path.join(output_dir, "fig02_x_y_rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 3: Signed Bias vs SNR
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax1.plot(m_data["snr_db"], m_data["bias_x"], marker='o', label=m)
            ax2.plot(m_data["snr_db"], m_data["bias_y"], marker='s', label=m)
    ax1.set_xlabel("SNR (dB)", fontsize=11)
    ax1.set_ylabel("Bias X (px)", fontsize=11)
    ax1.set_title("Signed X Bias vs SNR", fontsize=12, fontweight='bold')
    ax1.axhline(0, color='black', linestyle=':', alpha=0.5)
    ax1.legend(fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.set_xlabel("SNR (dB)", fontsize=11)
    ax2.set_ylabel("Bias Y (px)", fontsize=11)
    ax2.set_title("Signed Y Bias vs SNR", fontsize=12, fontweight='bold')
    ax2.axhline(0, color='black', linestyle=':', alpha=0.5)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    fig.suptitle("Figure 3: Signed Localization Bias (X and Y) vs SNR", fontsize=14, fontweight='bold')
    fig.savefig(os.path.join(output_dir, "fig03_bias_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 4: Error vs Fractional X Phase (phi_x)
    fig, ax = plt.subplots(figsize=(9, 6))
    if not df_phase.empty:
        for m in df_phase["method_name"].unique():
            px_data = df_phase[df_phase["method_name"] == m].groupby("phi_x")["mean_error_x"].mean().reset_index()
            ax.plot(px_data["phi_x"], px_data["mean_error_x"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("Fractional X Phase (ϕx)", fontsize=12)
        ax.set_ylabel("Mean X Error (px)", fontsize=12)
        ax.set_title("Figure 4: Systematic Subpixel Localization Bias vs Fractional X Phase", fontsize=14, fontweight='bold')
        ax.axhline(0, color='black', linestyle=':', alpha=0.5)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig04_error_vs_fractional_x_phase.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 5: Error vs Fractional Y Phase (phi_y)
    fig, ax = plt.subplots(figsize=(9, 6))
    if not df_phase.empty:
        for m in df_phase["method_name"].unique():
            py_data = df_phase[df_phase["method_name"] == m].groupby("phi_y")["mean_error_y"].mean().reset_index()
            ax.plot(py_data["phi_y"], py_data["mean_error_y"], marker='s', linewidth=2, label=m)
        ax.set_xlabel("Fractional Y Phase (ϕy)", fontsize=12)
        ax.set_ylabel("Mean Y Error (px)", fontsize=12)
        ax.set_title("Figure 5: Systematic Subpixel Localization Bias vs Fractional Y Phase", fontsize=14, fontweight='bold')
        ax.axhline(0, color='black', linestyle=':', alpha=0.5)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig05_error_vs_fractional_y_phase.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 6: Two-Dimensional Subpixel Bias Heatmaps
    if heatmaps_dict:
        n_methods = len(heatmaps_dict)
        fig, axes = plt.subplots(1, n_methods, figsize=(4 * n_methods, 4))
        if n_methods == 1:
            axes = [axes]
        steps = DEFAULT_PHASE_STEPS
        for idx, (m_name, hm_data) in enumerate(heatmaps_dict.items()):
            im = axes[idx].imshow(hm_data["heatmap_r"], extent=[0, 1, 0, 1], origin='lower', cmap='viridis')
            axes[idx].set_title(m_name, fontsize=11, fontweight='bold')
            axes[idx].set_xlabel("ϕx", fontsize=10)
            if idx == 0:
                axes[idx].set_ylabel("ϕy", fontsize=10)
            fig.colorbar(im, ax=axes[idx], fraction=0.046, pad=0.04)
        fig.suptitle("Figure 6: 2D Radial Subpixel Error Heatmaps over Fractional Phase Grid (ϕx, ϕy)", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "fig06_2d_subpixel_bias_heatmaps.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 7: PSF Width vs Localization Accuracy
    fig, ax = plt.subplots(figsize=(9, 6))
    f7_df = df_summary[df_summary.get("experiment_sub_id", "") == "8C_psf_sigma"]
    if not f7_df.empty:
        for m in f7_df["method_name"].unique():
            m_data = f7_df[f7_df["method_name"] == m].sort_values("sigma_x")
            ax.plot(m_data["sigma_x"], m_data["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("PSF Width Sigma (px)", fontsize=12)
        ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
        ax.set_title("Figure 7: Radial Pixel RMSE vs PSF Width Sigma", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig07_psf_width_vs_localization_accuracy.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 8: Localization Success Rate vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["success_rate"] * 100.0, marker='d', linewidth=2, label=m)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Localization Success Rate (%)", fontsize=12)
    ax.set_title("Figure 8: Localization Success Rate vs Configured SNR", fontsize=14, fontweight='bold')
    ax.set_ylim(-5, 105)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig08_success_rate_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 9: Angular Localization RMSE vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["angular_rmse_urad"], marker='^', linewidth=2, label=m)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Angular RMSE (μrad)", fontsize=12)
    ax.set_title("Figure 9: Angular Localization RMSE (μrad) vs SNR", fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig09_angular_rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 10: Error Distributions
    fig, ax = plt.subplots(figsize=(9, 6))
    if not df_raw.empty and "radial_error" in df_raw.columns:
        valid_raw = df_raw[df_raw["success"] == True]
        data_to_plot = []
        labels = []
        for m in valid_raw["method_name"].unique():
            errs = valid_raw[valid_raw["method_name"] == m]["radial_error"].dropna().values
            if len(errs) > 0:
                data_to_plot.append(errs)
                labels.append(m)
        if len(data_to_plot) > 0:
            try:
                ax.boxplot(data_to_plot, tick_labels=labels, showfliers=False)
            except TypeError:
                ax.boxplot(data_to_plot, labels=labels, showfliers=False)
            ax.set_ylabel("Radial Pixel Error (px)", fontsize=12)
            ax.set_title("Figure 10: Empirical Distribution of Subpixel Radial Errors", fontsize=14, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.7)
            fig.savefig(os.path.join(output_dir, "fig10_error_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 11: Background Sensitivity
    fig, ax = plt.subplots(figsize=(9, 6))
    f11_df = df_summary[df_summary.get("experiment_sub_id", "") == "8B_background"]
    if not f11_df.empty:
        for m in f11_df["method_name"].unique():
            m_data = f11_df[f11_df["method_name"] == m].sort_values("background_level")
            ax.plot(m_data["background_level"], m_data["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("Uniform Background Level", fontsize=12)
        ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
        ax.set_title("Figure 11: Subpixel Localization RMSE vs Background Level", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig11_background_sensitivity.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 12: ROI-Size Sensitivity
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    f12_df = df_summary[df_summary.get("experiment_sub_id", "") == "8D_roi"]
    if not f12_df.empty:
        for m in f12_df["method_name"].unique():
            m_data = f12_df[f12_df["method_name"] == m].sort_values("roi_size")
            ax1.plot(m_data["roi_size"], m_data["radial_rmse"], marker='o', label=m)
            ax2.plot(m_data["roi_size"], m_data["success_rate"] * 100.0, marker='s', label=m)
        ax1.set_xlabel("ROI Size (px)", fontsize=11)
        ax1.set_ylabel("Radial Pixel RMSE (px)", fontsize=11)
        ax1.set_title("Radial RMSE vs ROI Size", fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, linestyle='--', alpha=0.7)

        ax2.set_xlabel("ROI Size (px)", fontsize=11)
        ax2.set_ylabel("Success Rate (%)", fontsize=11)
        ax2.set_title("Success Rate vs ROI Size", fontsize=12, fontweight='bold')
        ax2.set_ylim(-5, 105)
        ax2.legend(fontsize=9)
        ax2.grid(True, linestyle='--', alpha=0.7)

        fig.suptitle("Figure 12: ROI-Size Sensitivity (Subpixel Accuracy & Success Rate)", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "fig12_roi_size_sensitivity.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
