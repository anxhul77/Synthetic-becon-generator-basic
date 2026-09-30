import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def generate_all_experiment_7_plots(df_summary: pd.DataFrame, df_raw: pd.DataFrame, df_paired: pd.DataFrame, output_dir: str):
    """
    Generates Figures 1-12 for Experiment 7 with publication quality styling.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # Figure 1: Radial RMSE vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    f1_df = df_summary[df_summary.get("scenario_id", "").str.startswith("7A_snr") | (df_summary.get("experiment_sub_id", "") == "7A")]
    if f1_df.empty and "snr_db" in df_summary.columns:
        f1_df = df_summary

    methods = f1_df["method_name"].unique() if "method_name" in f1_df.columns else []
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

    # Figure 2: Mean Radial Error vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["mean_radial_error"], marker='s', linewidth=2, label=m)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Mean Radial Error (px)", fontsize=12)
    ax.set_title("Figure 2: Mean Radial Pixel Error vs Configured SNR", fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig02_mean_radial_error_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 3: X and Y Localization Bias vs SNR
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
    fig.savefig(os.path.join(output_dir, "fig03_localization_bias_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 4: Angular RMSE vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["angular_rmse_urad"], marker='^', linewidth=2, label=m)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Angular RMSE (μrad)", fontsize=12)
    ax.set_title("Figure 4: Angular Localization RMSE (μrad) vs SNR", fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig04_angular_rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 5: Localization Success Rate vs SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_data = f1_df[f1_df["method_name"] == m].sort_values("snr_db")
        if not m_data.empty:
            ax.plot(m_data["snr_db"], m_data["success_rate"] * 100.0, marker='d', linewidth=2, label=m)
    ax.set_xlabel("Configured SNR (dB)", fontsize=12)
    ax.set_ylabel("Localization Success Rate (%)", fontsize=12)
    ax.set_title("Figure 5: Localization Success Rate vs Configured SNR", fontsize=14, fontweight='bold')
    ax.set_ylim(-5, 105)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "fig05_success_rate_vs_snr.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 6: Localization Accuracy vs Uniform Background Level
    fig, ax = plt.subplots(figsize=(9, 6))
    f6_df = df_summary[df_summary.get("experiment_sub_id", "") == "7B_uniform"]
    if not f6_df.empty:
        for m in f6_df["method_name"].unique():
            m_data = f6_df[f6_df["method_name"] == m].sort_values("background_level")
            ax.plot(m_data["background_level"], m_data["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("Uniform Background Level", fontsize=12)
        ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
        ax.set_title("Figure 6: Radial Pixel RMSE vs Uniform Background Level", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig06_rmse_vs_background.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 7: Gradient Background Robustness
    fig, ax = plt.subplots(figsize=(9, 6))
    f7_df = df_summary[df_summary.get("experiment_sub_id", "") == "7B_gradient"]
    if not f7_df.empty:
        grad_scens = f7_df["scenario_id"].unique()
        x_pos = np.arange(len(grad_scens))
        w = 0.15
        for idx, m in enumerate(f7_df["method_name"].unique()):
            m_vals = []
            for sc in grad_scens:
                v = f7_df[(f7_df["scenario_id"] == sc) & (f7_df["method_name"] == m)]["radial_rmse"].values
                m_vals.append(v[0] if len(v) > 0 else 0.0)
            ax.bar(x_pos + idx * w, m_vals, width=w, label=m)
        ax.set_xticks(x_pos + w * 2)
        ax.set_xticklabels(grad_scens, fontsize=10)
        ax.set_xlabel("Gradient Scenario", fontsize=12)
        ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
        ax.set_title("Figure 7: Localization RMSE under Spatial Background Gradients", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig07_gradient_background_robustness.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 8: PSF Robustness
    fig, ax = plt.subplots(figsize=(9, 6))
    f8_df = df_summary[df_summary.get("experiment_sub_id", "") == "7C_psf"]
    if not f8_df.empty:
        psf_types = f8_df["psf_condition"].unique()
        x_pos = np.arange(len(psf_types))
        w = 0.15
        for idx, m in enumerate(f8_df["method_name"].unique()):
            m_vals = []
            for pt in psf_types:
                v = f8_df[(f8_df["psf_condition"] == pt) & (f8_df["method_name"] == m)]["radial_rmse"].values
                m_vals.append(v[0] if len(v) > 0 else 0.0)
            ax.bar(x_pos + idx * w, m_vals, width=w, label=m)
        ax.set_xticks(x_pos + w * 2)
        ax.set_xticklabels(psf_types, fontsize=10)
        ax.set_xlabel("PSF Condition", fontsize=12)
        ax.set_ylabel("Radial Pixel RMSE (px)", fontsize=12)
        ax.set_title("Figure 8: Localization RMSE across PSF Model Variations", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig08_psf_robustness.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 9: Latency Comparison
    fig, ax = plt.subplots(figsize=(9, 6))
    if "mean_latency_ms" in df_summary.columns:
        m_lat = df_summary.groupby("method_name")[["mean_latency_ms", "median_latency_ms", "p95_latency_ms"]].mean()
        x_pos = np.arange(len(m_lat))
        w = 0.25
        ax.bar(x_pos, m_lat["mean_latency_ms"], width=w, label="Mean Latency")
        ax.bar(x_pos + w, m_lat["median_latency_ms"], width=w, label="Median Latency")
        ax.bar(x_pos + 2*w, m_lat["p95_latency_ms"], width=w, label="95th Pct Latency")
        ax.set_xticks(x_pos + w)
        ax.set_xticklabels(m_lat.index, fontsize=10, rotation=15)
        ax.set_ylabel("Latency (ms)", fontsize=12)
        ax.set_title("Figure 9: Computational Latency Comparison across Algorithms", fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig09_latency_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 10: ROI Size Sensitivity
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    f10_df = df_summary[df_summary.get("experiment_sub_id", "") == "7D_roi"]
    if not f10_df.empty:
        for m in f10_df["method_name"].unique():
            m_data = f10_df[f10_df["method_name"] == m].sort_values("roi_size")
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

        fig.suptitle("Figure 10: ROI Size Sensitivity (Accuracy and Success Rate)", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "fig10_roi_size_sensitivity.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 11: Subpixel Localization Bias
    fig, ax = plt.subplots(figsize=(9, 6))
    f11_df = df_summary[df_summary.get("experiment_sub_id", "") == "7E_subpixel"]
    if not f11_df.empty:
        for m in f11_df["method_name"].unique():
            m_data = f11_df[f11_df["method_name"] == m].sort_values("subpixel_offset")
            ax.plot(m_data["subpixel_offset"], m_data["bias_x"], marker='o', label=f"{m} (Bias X)")
            ax.plot(m_data["subpixel_offset"], m_data["bias_y"], marker='x', linestyle='--', label=f"{m} (Bias Y)")
        ax.set_xlabel("Subpixel Offset Phase (px)", fontsize=12)
        ax.set_ylabel("Signed Bias (px)", fontsize=12)
        ax.set_title("Figure 11: Subpixel Systematic Localization Bias vs Fractional Phase", fontsize=14, fontweight='bold')
        ax.axhline(0, color='black', linestyle=':', alpha=0.5)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "fig11_subpixel_localization_bias.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 12: Error Distribution
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
            ax.set_title("Figure 12: Empirical Distribution of Radial Localization Errors", fontsize=14, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.7)
            fig.savefig(os.path.join(output_dir, "fig12_error_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
