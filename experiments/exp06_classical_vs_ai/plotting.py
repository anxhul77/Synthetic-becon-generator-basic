import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def generate_exp06_figures(df_predictions: pd.DataFrame,
                           df_summary: pd.DataFrame,
                           df_paired: pd.DataFrame,
                           output_dir: str = "results/exp06_classical_vs_ai/figures"):
    """
    Generates 10 publication-quality diagnostic plots for Experiment 06.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    color_map = {
        "classical": "#1f77b4",  # Blue
        "ai": "#ff7f0e",         # Orange
        "hybrid": "#2ca02c"      # Green
    }
    label_map = {
        "classical": "Classical Detector",
        "ai": "AI Heatmap Detector",
        "hybrid": "Hybrid Fused Detector"
    }

    # -------------------------------------------------------------
    # Fig 01: Detection probability vs SNR
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    snr_levels = [30.0, 20.0, 15.0, 10.0, 5.0, 0.0]
    
    for det in ["classical", "ai", "hybrid"]:
        pd_vals, err_lows, err_highs = [], [], []
        for snr in snr_levels:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(f"snr{int(snr)}"))]
            if len(sub) > 0:
                p = float(sub["pd"].mean())
                p_low = float(sub["pd_ci_low"].mean())
                p_high = float(sub["pd_ci_high"].mean())
            else:
                p, p_low, p_high = 0.0, 0.0, 0.0
            pd_vals.append(p)
            err_lows.append(p - p_low)
            err_highs.append(p_high - p)
        
        ax.errorbar(snr_levels, pd_vals, yerr=[err_lows, err_highs],
                    label=label_map[det], color=color_map[det], marker='o', capsize=4, linewidth=2)

    ax.set_xlabel("SNR (dB)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Detection Probability ($P_D$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 1: Detection Probability vs SNR (with 95% Wilson CIs)", fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig01_pd_vs_snr.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 02: False-alarm probability vs SNR
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    for det in ["classical", "ai", "hybrid"]:
        pfa_vals = []
        for snr in snr_levels:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(f"snr{int(snr)}"))]
            pfa_vals.append(float(sub["pfa"].mean()) if len(sub) > 0 else 0.0)
        ax.plot(snr_levels, pfa_vals, label=label_map[det], color=color_map[det], marker='s', linewidth=2)

    ax.set_xlabel("SNR (dB)", fontsize=11, fontweight='bold')
    ax.set_ylabel("False Alarm Rate ($P_{FA}$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 2: False Alarm Probability ($P_{FA}$) vs SNR", fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig02_pfa_vs_snr.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 03: Precision, Recall, F1 comparison
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    mets = ["precision", "recall", "f1"]
    x = np.arange(len(mets))
    width = 0.25

    for idx, det in enumerate(["classical", "ai", "hybrid"]):
        sub = df_summary[df_summary["detector"] == det]
        prec = float(sub["precision"].mean()) if len(sub) > 0 else 0.0
        rec = float(sub["recall"].mean()) if len(sub) > 0 else 0.0
        f1_score = float(sub["f1"].mean()) if len(sub) > 0 else 0.0
        ax.bar(x + idx * width, [prec, rec, f1_score], width, label=label_map[det], color=color_map[det])

    ax.set_ylabel("Score", fontsize=11, fontweight='bold')
    ax.set_title("Figure 3: Overall Precision, Recall, and F1 Score", fontsize=12, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(["Precision", "Recall", "F1 Score"], fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig03_precision_recall_f1.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 04: Performance vs Background Level
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    bg_levels = [0.0, 50.0, 100.0, 200.0, 500.0]
    for det in ["classical", "ai", "hybrid"]:
        pd_vals = []
        for bg in bg_levels:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(f"bg{int(bg)}"))]
            pd_vals.append(float(sub["pd"].mean()) if len(sub) > 0 else 0.0)
        ax.plot(bg_levels, pd_vals, label=label_map[det], color=color_map[det], marker='^', linewidth=2)

    ax.set_xlabel("Background Level (DN)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Detection Probability ($P_D$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 4: Detection Performance vs Ambient Background Level", fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig04_pd_vs_background.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 05: Gradient Background Robustness
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    grad_types = ["uniform", "horizontal", "vertical", "twod"]
    x = np.arange(len(grad_types))
    width = 0.25

    for idx, det in enumerate(["classical", "ai", "hybrid"]):
        pd_vals = []
        for gt_type in grad_types:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(gt_type))]
            pd_vals.append(float(sub["pd"].mean()) if len(sub) > 0 else 0.0)
        ax.bar(x + idx * width, pd_vals, width, label=label_map[det], color=color_map[det])

    ax.set_xlabel("Spatial Background Gradient Type", fontsize=11, fontweight='bold')
    ax.set_ylabel("Detection Probability ($P_D$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 5: Robustness Across Spatial Background Gradients", fontsize=12, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(["Uniform", "Horizontal", "Vertical", "2D Gradient"], fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig05_gradient_robustness.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 06: Clutter / Distractor Robustness
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    dist_counts = [0, 1, 3, 5]
    for det in ["classical", "ai", "hybrid"]:
        pd_vals = []
        for d_c in dist_counts:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(f"dist{d_c}"))]
            pd_vals.append(float(sub["pd"].mean()) if len(sub) > 0 else 0.0)
        ax.plot(dist_counts, pd_vals, label=label_map[det], color=color_map[det], marker='D', linewidth=2)

    ax.set_xlabel("Number of Bright Distractor Objects", fontsize=11, fontweight='bold')
    ax.set_ylabel("Detection Probability ($P_D$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 6: Robustness Against Optical Clutter / Distractors", fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig06_clutter_robustness.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 07: PSF Robustness
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    psf_types = ["gaussian", "elliptical"]
    x = np.arange(len(psf_types))
    width = 0.25

    for idx, det in enumerate(["classical", "ai", "hybrid"]):
        pd_vals = []
        for psf in psf_types:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(psf))]
            pd_vals.append(float(sub["pd"].mean()) if len(sub) > 0 else 0.0)
        ax.bar(x + idx * width, pd_vals, width, label=label_map[det], color=color_map[det])

    ax.set_xlabel("Optical Point Spread Function (PSF) Shape", fontsize=11, fontweight='bold')
    ax.set_ylabel("Detection Probability ($P_D$)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 7: Detection Performance Across PSF Variations", fontsize=12, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(["Isotropic Gaussian", "Elliptical Gaussian"], fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig07_psf_robustness.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 08: Latency comparison
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    lat_means = []
    lat_p95s = []
    dets = ["classical", "ai", "hybrid"]
    for det in dets:
        sub = df_summary[df_summary["detector"] == det]
        lat_means.append(float(sub["latency_mean_ms"].mean()) if len(sub) > 0 else 0.0)
        lat_p95s.append(float(sub["latency_p95_ms"].mean()) if len(sub) > 0 else 0.0)

    x = np.arange(len(dets))
    width = 0.35
    ax.bar(x - width/2, lat_means, width, label="Mean Latency (ms)", color="#1f77b4")
    ax.bar(x + width/2, lat_p95s, width, label="95th Percentile Latency (ms)", color="#ff7f0e")

    ax.set_ylabel("Latency (ms)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 8: Steady-State Inference Latency Breakdown (Batch Size = 1)", fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(["Classical", "AI Heatmap", "Hybrid Fused"], fontweight='bold')
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig08_latency_comparison.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 09: Localization Accuracy (Radial RMSE)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    for det in ["classical", "ai", "hybrid"]:
        rmse_vals = []
        for snr in snr_levels:
            sub = df_summary[(df_summary["detector"] == det) & (df_summary["scenario_id"].str.contains(f"snr{int(snr)}"))]
            rmse_vals.append(float(sub["rmse_px"].mean()) if len(sub) > 0 else np.nan)
        ax.plot(snr_levels, rmse_vals, label=label_map[det], color=color_map[det], marker='o', linewidth=2)

    ax.set_xlabel("SNR (dB)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Sub-Pixel Radial RMSE (pixels)", fontsize=11, fontweight='bold')
    ax.set_title("Figure 9: Sub-Pixel Beacon Localization RMSE vs SNR", fontsize=12, fontweight='bold')
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig09_localization_rmse.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # Fig 10: Performance Heatmap Matrix
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    snr_grid = [30.0, 20.0, 15.0, 10.0, 5.0]
    bg_grid = [0.0, 50.0, 100.0, 200.0, 500.0]

    for idx, det in enumerate(["classical", "ai", "hybrid"]):
        grid_data = np.zeros((len(bg_grid), len(snr_grid)))
        for r, bg in enumerate(bg_grid):
            for c, snr in enumerate(snr_grid):
                sub = df_summary[(df_summary["detector"] == det) &
                                 (df_summary["scenario_id"].str.contains(f"snr{int(snr)}")) &
                                 (df_summary["scenario_id"].str.contains(f"bg{int(bg)}"))]
                grid_data[r, c] = float(sub["pd"].mean()) if len(sub) > 0 else 0.0

        im = axes[idx].imshow(grid_data, cmap="viridis", vmin=0.0, vmax=1.0)
        axes[idx].set_title(label_map[det], fontsize=11, fontweight='bold')
        axes[idx].set_xticks(np.arange(len(snr_grid)))
        axes[idx].set_xticklabels([f"{int(s)} dB" for s in snr_grid])
        axes[idx].set_yticks(np.arange(len(bg_grid)))
        axes[idx].set_yticklabels([f"{int(b)} DN" for b in bg_grid])
        axes[idx].set_xlabel("SNR Level", fontweight='bold')
        if idx == 0:
            axes[idx].set_ylabel("Background Level", fontweight='bold')

        # Annotate cell values
        for r in range(len(bg_grid)):
            for c in range(len(snr_grid)):
                axes[idx].text(c, r, f"{grid_data[r, c]:.2f}", ha="center", va="center", color="w" if grid_data[r, c] < 0.5 else "k", fontsize=9)

    fig.suptitle("Figure 10: Detection Probability ($P_D$) Heatmap Matrix Across SNR and Background Levels", fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig10_performance_matrix.png"), dpi=300)
    plt.close()

    print(f"Generated 10 diagnostic figures in {output_dir}.", flush=True)
