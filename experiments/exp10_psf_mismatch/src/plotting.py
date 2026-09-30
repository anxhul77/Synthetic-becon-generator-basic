import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def _safe_legend(ax, **kwargs):
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(**kwargs)

def generate_all_experiment_10_plots(
    df_summary: pd.DataFrame,
    df_raw: pd.DataFrame,
    df_paired: pd.DataFrame,
    df_mismatch: pd.DataFrame,
    df_phase: pd.DataFrame,
    heatmaps_dict: dict,
    output_dir: str
):
    """
    Generates publication-quality figures for Experiment 10: PSF Mismatch and Localization Robustness.
    Saves all plots to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    methods = df_summary["method_name"].unique() if "method_name" in df_summary.columns else []

    # Figure 1: Localization RMSE vs Mismatch Strength by PSF Family
    psf_families = [f for f in df_summary["psf_family"].unique() if pd.notna(f)] if "psf_family" in df_summary.columns else []
    if psf_families:
        n_fams = len(psf_families)
        fig, axes = plt.subplots(1, n_fams, figsize=(4.5 * n_fams, 4.5), sharey=False)
        if n_fams == 1:
            axes = [axes]
        for idx, fam in enumerate(psf_families):
            ax = axes[idx]
            fam_df = df_summary[df_summary["psf_family"] == fam]
            for m in methods:
                m_df = fam_df[fam_df["method_name"] == m].sort_values("mismatch_strength")
                if not m_df.empty:
                    ax.plot(m_df["mismatch_strength"], m_df["radial_rmse"], marker='o', linewidth=2, label=m)
            ax.set_xlabel("Mismatch Strength", fontsize=10)
            if idx == 0:
                ax.set_ylabel("Radial RMSE (pixels)", fontsize=10)
            ax.set_title(f"PSF: {fam.replace('_', ' ').title()}", fontsize=11, fontweight='bold')
            _safe_legend(ax, fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.7)
        fig.suptitle("Figure 1: Localization RMSE vs Mismatch Strength across PSF Families", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "rmse_vs_mismatch.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 2: RMSE by PSF Family Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df_summary.empty:
        summary_by_fam = df_summary.groupby(["psf_family", "method_name"])["radial_rmse"].mean().reset_index()
        fams = sorted(summary_by_fam["psf_family"].unique())
        x = np.arange(len(fams))
        width = 0.25
        for idx, m in enumerate(methods):
            m_vals = [summary_by_fam[(summary_by_fam["psf_family"] == f) & (summary_by_fam["method_name"] == m)]["radial_rmse"].values for f in fams]
            m_means = [v[0] if len(v) > 0 else 0.0 for v in m_vals]
            ax.bar(x + idx * width, m_means, width, label=m)
        ax.set_xticks(x + width)
        ax.set_xticklabels([f.replace('_', ' ').title() for f in fams], fontsize=10)
        ax.set_ylabel("Mean Radial RMSE (pixels)", fontsize=12)
        ax.set_title("Figure 2: Mean Localization RMSE Comparison across PSF Families", fontsize=14, fontweight='bold')
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "rmse_by_psf_family.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 3: Gaussian Mismatch Penalty
    if not df_mismatch.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        for fam in df_mismatch["psf_family"].unique():
            fam_m = df_mismatch[df_mismatch["psf_family"] == fam].sort_values("mismatch_strength")
            ax.plot(fam_m["mismatch_strength"], fam_m["absolute_mismatch_penalty"], marker='s', linewidth=2, label=f"PSF: {fam}")
        ax.set_xlabel("Mismatch Strength Parameter", fontsize=12)
        ax.set_ylabel("Gaussian RMSE Penalty (pixels above matched baseline)", fontsize=12)
        ax.set_title("Figure 3: Gaussian Fitting Mismatch Penalty", fontsize=14, fontweight='bold')
        ax.axhline(0, color='black', linestyle=':', alpha=0.5)
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "mismatch_penalty.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 4: Gaussian vs PSF-Aware Localization Improvement
    if not df_paired.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        for fam in df_paired["psf_family"].unique() if "psf_family" in df_paired.columns else ["all"]:
            p_fam = df_paired[df_paired.get("psf_family", fam) == fam] if "psf_family" in df_paired.columns else df_paired
            p_g_psf = p_fam[(p_fam["method_a"].str.contains("Gaussian")) & (p_fam["method_b"].str.contains("PSF"))]
            if not p_g_psf.empty and "mismatch_strength" in p_g_psf.columns:
                ax.plot(p_g_psf["mismatch_strength"], p_g_psf["rmse_difference"], marker='o', linewidth=2, label=f"Improvement ({fam})")
        ax.set_xlabel("Mismatch Strength Parameter", fontsize=12)
        ax.set_ylabel("Paired RMSE Improvement (Gaussian - PSF-Aware) (pixels)", fontsize=12)
        ax.set_title("Figure 4: Localization Accuracy Advantage of PSF-Aware Fitting", fontsize=14, fontweight='bold')
        ax.axhline(0, color='black', linestyle=':', alpha=0.5)
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "gaussian_vs_psf_aware.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 5: Localization Bias vs Mismatch
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for m in methods:
        m_summary = df_summary[df_summary["method_name"] == m].groupby("mismatch_strength")[["bias_x", "bias_y"]].mean().reset_index()
        if not m_summary.empty:
            ax1.plot(m_summary["mismatch_strength"], m_summary["bias_x"], marker='o', label=m)
            ax2.plot(m_summary["mismatch_strength"], m_summary["bias_y"], marker='s', label=m)
    ax1.set_xlabel("Mismatch Strength", fontsize=11)
    ax1.set_ylabel("Signed Bias X (pixels)", fontsize=11)
    ax1.set_title("Signed X Bias vs Mismatch", fontsize=12, fontweight='bold')
    ax1.axhline(0, color='black', linestyle=':', alpha=0.5)
    _safe_legend(ax1, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.set_xlabel("Mismatch Strength", fontsize=11)
    ax2.set_ylabel("Signed Bias Y (pixels)", fontsize=11)
    ax2.set_title("Signed Y Bias vs Mismatch", fontsize=12, fontweight='bold')
    ax2.axhline(0, color='black', linestyle=':', alpha=0.5)
    _safe_legend(ax2, fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    fig.suptitle("Figure 5: Systematic Localization Bias vs PSF Mismatch", fontsize=14, fontweight='bold')
    fig.savefig(os.path.join(output_dir, "bias_vs_mismatch.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 6: Success Rate vs Mismatch
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_succ = df_summary[df_summary["method_name"] == m].groupby("mismatch_strength")["success_rate"].mean().reset_index()
        if not m_succ.empty:
            ax.plot(m_succ["mismatch_strength"], m_succ["success_rate"] * 100.0, marker='d', linewidth=2, label=m)
    ax.set_xlabel("Mismatch Strength", fontsize=12)
    ax.set_ylabel("Localization Success Rate (%)", fontsize=12)
    ax.set_title("Figure 6: Fitting Success Rate vs PSF Mismatch", fontsize=14, fontweight='bold')
    ax.set_ylim(-5, 105)
    _safe_legend(ax, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "success_rate_vs_mismatch.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 7: Latency Comparison across Methods & PSF Families
    fig, ax = plt.subplots(figsize=(9, 6))
    for m in methods:
        m_lat = df_summary[df_summary["method_name"] == m].groupby("psf_family")["mean_latency_ms"].mean().reset_index()
        if not m_lat.empty:
            ax.bar(m_lat["psf_family"].apply(lambda f: f.replace('_', ' ').title()), m_lat["mean_latency_ms"], label=m, alpha=0.7)
    ax.set_ylabel("Mean Latency (ms)", fontsize=12)
    ax.set_title("Figure 7: Computational Latency Comparison across Estimators", fontsize=14, fontweight='bold')
    _safe_legend(ax, fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    fig.savefig(os.path.join(output_dir, "latency_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Figure 8: RMSE vs SNR under PSF Mismatch
    snr_df = df_summary[df_summary.get("experiment_sub_id", "") == "10F_snr"]
    if not snr_df.empty:
        fig, ax = plt.subplots(figsize=(9, 6))
        for m in methods:
            m_snr = snr_df[snr_df["method_name"] == m].groupby("snr_db")["radial_rmse"].mean().reset_index()
            if not m_snr.empty:
                ax.plot(m_snr["snr_db"], m_snr["radial_rmse"], marker='o', linewidth=2, label=m)
        ax.set_xlabel("Configured SNR (dB)", fontsize=12)
        ax.set_ylabel("Radial Localization RMSE (pixels)", fontsize=12)
        ax.set_title("Figure 8: Localization RMSE vs SNR under PSF Mismatch", fontsize=14, fontweight='bold')
        _safe_legend(ax, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        fig.savefig(os.path.join(output_dir, "rmse_vs_snr.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 9: Subpixel Phase Error Heatmaps
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
        fig.suptitle("Figure 9: Subpixel Phase Error Heatmaps under PSF Mismatch", fontsize=14, fontweight='bold')
        fig.savefig(os.path.join(output_dir, "phase_error_heatmaps.png"), dpi=300, bbox_inches='tight')
        plt.close(fig)

    # Figure 10: Localization Error Distributions
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df_raw.empty and "radial_error_px" in df_raw.columns:
        valid_raw = df_raw[df_raw["success"] == True]
        data_to_plot = []
        labels = []
        for fam in sorted(valid_raw["psf_family"].dropna().unique()):
            for m in methods:
                errs = valid_raw[(valid_raw["psf_family"] == fam) & (valid_raw["method_name"] == m)]["radial_error_px"].dropna().values
                if len(errs) > 0:
                    data_to_plot.append(errs)
                    labels.append(f"{fam[:4]}\n{m[:5]}")
        if len(data_to_plot) > 0:
            try:
                ax.boxplot(data_to_plot, tick_labels=labels, showfliers=False)
            except TypeError:
                ax.boxplot(data_to_plot, labels=labels, showfliers=False)
            ax.set_ylabel("Radial Error (pixels)", fontsize=12)
            ax.set_title("Figure 10: Localization Error Distributions by PSF Family & Estimator", fontsize=14, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.7)
            fig.savefig(os.path.join(output_dir, "error_distributions.png"), dpi=300, bbox_inches='tight')
    plt.close(fig)
