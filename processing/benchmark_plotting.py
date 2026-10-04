"""
Pure Matplotlib Publication-Quality Plotting Suite for Dual Evaluation Benchmark.

Generates figures 1-4:
1. Fig 1: Estimator-Only vs End-to-End Benchmark Radial RMSE.
2. Fig 2: PSF Model Mismatch Performance across 6 conditions.
3. Fig 3: ROI Center Misalignment Offset across ROI Providers.
4. Fig 4: Subpixel Radial RMSE vs SNR.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate_all_dual_benchmark_plots(df_summary: pd.DataFrame, df_raw: pd.DataFrame, output_dir: str):
    """Generates figures 1-4 using standard Matplotlib."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('ggplot')

    # -------------------------------------------------------------
    # Fig 1: Estimator-Only vs End-to-End Benchmark Radial RMSE
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 6))
    sub1 = df_summary[df_summary["snr_db"] == 15.0]
    if not sub1.empty:
        estimators = sub1["estimator_name"].unique()
        categories = sub1["eval_category"].unique()
        x = np.arange(len(estimators))
        width = 0.35 if len(categories) > 1 else 0.5

        for i, cat in enumerate(categories):
            cat_df = sub1[sub1["eval_category"] == cat]
            rmse_vals = [
                cat_df[cat_df["estimator_name"] == est]["radial_rmse"].mean()
                if not cat_df[cat_df["estimator_name"] == est].empty else 0.0
                for est in estimators
            ]
            offset = (i - len(categories) / 2.0 + 0.5) * width
            ax.bar(x + offset, rmse_vals, width, label=cat)

        ax.set_title("Fig 1: Estimator-Only (Ground-Truth ROI) vs End-to-End Benchmark Radial RMSE (SNR = 15 dB)", fontsize=13, fontweight='bold')
        ax.set_xlabel("Subpixel Localization Estimator", fontsize=11)
        ax.set_ylabel("Radial RMSE (pixels)", fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(estimators, rotation=20, ha="right")
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig01_estimator_only_vs_end_to_end_rmse.png"), dpi=300)
    plt.close(fig)

    # -------------------------------------------------------------
    # Fig 2: PSF Model Mismatch Performance Across 6 Conditions
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 7))
    sub2 = df_summary[(df_summary["snr_db"] == 15.0) & (df_summary["eval_category"] == "End-to-End Benchmark")]
    if not sub2.empty:
        psf_conds = sub2["psf_condition"].unique()
        estimators = sub2["estimator_name"].unique()
        x = np.arange(len(psf_conds))
        width = 0.8 / max(1, len(estimators))

        for i, est in enumerate(estimators):
            est_df = sub2[sub2["estimator_name"] == est]
            rmse_vals = [
                est_df[est_df["psf_condition"] == cond]["radial_rmse"].mean()
                if not est_df[est_df["psf_condition"] == cond].empty else 0.0
                for cond in psf_conds
            ]
            offset = (i - len(estimators) / 2.0 + 0.5) * width
            ax.bar(x + offset, rmse_vals, width, label=est)

        ax.set_title("Fig 2: Localization Error under PSF Model Mismatch Conditions (End-to-End Pipeline, SNR = 15 dB)", fontsize=13, fontweight='bold')
        ax.set_xlabel("Generated Image PSF Condition", fontsize=11)
        ax.set_ylabel("Radial RMSE (pixels)", fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(psf_conds, rotation=15, ha="right")
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig02_psf_model_mismatch_penalty.png"), dpi=300)
    plt.close(fig)

    # -------------------------------------------------------------
    # Fig 3: ROI Placement Offset Distributions (End-to-End ROI Providers)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    if not df_raw.empty:
        providers = df_raw["roi_provider_label"].unique()
        data_to_plot = [df_raw[df_raw["roi_provider_label"] == p]["roi_center_offset_px"].dropna() for p in providers]
        ax.boxplot(data_to_plot, tick_labels=providers, patch_artist=True)
        ax.set_title("Fig 3: ROI Placement Center Misalignment Offset across ROI Providers", fontsize=13, fontweight='bold')
        ax.set_xlabel("ROI Provider Category", fontsize=11)
        ax.set_ylabel("ROI Center Misalignment Offset (pixels)", fontsize=11)
        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig03_roi_center_offset_bias.png"), dpi=300)
    plt.close(fig)

    # -------------------------------------------------------------
    # Fig 4: Radial RMSE vs SNR (Estimator-Only vs End-to-End)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    sub4 = df_summary[df_summary["estimator_name"] == "Intensity-Weighted Centroid"]
    if not sub4.empty:
        cats = sub4["eval_category"].unique()
        for cat in cats:
            c_df = sub4[sub4["eval_category"] == cat].groupby("snr_db")["radial_rmse"].mean().reset_index()
            c_df = c_df.sort_values("snr_db", ascending=False)
            ax.plot(c_df["snr_db"], c_df["radial_rmse"], marker='o', linewidth=2, label=cat)

        ax.invert_xaxis()  # High SNR to low SNR
        ax.set_title("Fig 4: Subpixel Radial RMSE vs SNR (Estimator-Only vs End-to-End ROI Modes)", fontsize=13, fontweight='bold')
        ax.set_xlabel("Signal-to-Noise Ratio (dB)", fontsize=11)
        ax.set_ylabel("Radial RMSE (pixels)", fontsize=11)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "fig04_snr_degradation_e2e.png"), dpi=300)
    plt.close(fig)

    print(f"Generated 4 publication-quality benchmark figures in: {output_dir}")
