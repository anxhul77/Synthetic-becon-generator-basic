import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from scipy.stats import chi2
from typing import Dict, Any

from .ellipse_coverage import compute_ellipse_geometry

def plot_horizon_vs_coverage(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Empirical Coverage vs Prediction Horizon h (0.5s to 5s) for 50%, 90%, 95% confidence levels,
    including nominal reference lines and Wilson 95% confidence bounds.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    confidence_levels = [0.50, 0.90, 0.95]
    colors = {0.50: '#1f77b4', 0.90: '#ff7f0e', 0.95: '#2ca02c'}
    markers = {0.50: 'o', 0.90: 's', 0.95: '^'}

    horizons = sorted(summary_df['horizon_sec'].unique())

    for alpha in confidence_levels:
        sub = summary_df[summary_df['nominal_confidence'] == alpha].sort_values('horizon_sec')
        if len(sub) == 0:
            continue
        h_vals = sub['horizon_sec'].values
        cov_vals = sub['empirical_coverage'].values * 100.0
        ci_low = sub['ci_lower'].values * 100.0
        ci_high = sub['ci_upper'].values * 100.0

        yerr = [cov_vals - ci_low, ci_high - cov_vals]

        plt.errorbar(
            h_vals, cov_vals, yerr=yerr,
            label=f'Empirical {int(alpha*100)}% Coverage',
            color=colors[alpha], marker=markers[alpha], linewidth=2.0, capsize=4, markersize=7
        )
        plt.axhline(alpha * 100.0, color=colors[alpha], linestyle='--', alpha=0.7, label=f'Nominal {int(alpha*100)}% Ref')

    plt.title('Empirical Uncertainty Ellipse Coverage vs Prediction Horizon (0.5s - 5.0s)', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Prediction Horizon h [seconds]', fontsize=12, labelpad=8)
    plt.ylabel('Empirical Coverage [%]', fontsize=12, labelpad=8)
    plt.ylim([40, 102])
    plt.xticks(horizons)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='lower right', fontsize=10, framealpha=0.9)
    plt.tight_layout()

    fig_path = os.path.join(output_dir, 'horizon_vs_coverage.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_trajectory_ellipse_overlay(sample_trials: pd.DataFrame, output_dir: str):
    """
    Plots representative true vs predicted beacon positions with 95% uncertainty ellipses at 1s, 3s, and 5s horizons.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)

    chi2_95 = 5.991465

    # Filter sample trial at 5s horizon
    h_selected = [1.0, 3.0, 5.0]
    colors_h = {1.0: 'blue', 3.0: 'orange', 5.0: 'red'}

    # Draw true path if available
    true_x = sample_trials['gt_x_future'].values[:30]
    true_y = sample_trials['gt_y_future'].values[:30]
    ax.plot(true_x, true_y, 'k--', linewidth=1.5, alpha=0.6, label='True Future Trajectory')

    for idx, row in sample_trials.head(15).iterrows():
        h = row['horizon_sec']
        if h not in h_selected:
            continue
        pred_x, pred_y = row['pred_x'], row['pred_y']
        gt_x, gt_y = row['gt_x_future'], row['gt_y_future']

        Sigma_h = np.array([
            [row['sigma_uu'], row['sigma_uv']],
            [row['sigma_uv'], row['sigma_vv']]
        ])

        a, b, phi_deg = compute_ellipse_geometry(Sigma_h, chi2_95)

        ellipse = Ellipse(
            xy=(pred_x, pred_y), width=2*a, height=2*b, angle=phi_deg,
            edgecolor=colors_h[h], facecolor=colors_h[h], alpha=0.15, linewidth=1.5
        )
        ax.add_patch(ellipse)

        ax.scatter(pred_x, pred_y, color=colors_h[h], marker='o', s=40, label=f'Pred h={h}s' if idx < 3 else "")
        ax.scatter(gt_x, gt_y, color='black', marker='x', s=50, label='GT Future' if idx == 0 else "")

    ax.set_title('95% Uncertainty Ellipse Overlay across Horizons (1s, 3s, 5s)', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('Pixel Position U [px]', fontsize=12)
    ax.set_ylabel('Pixel Position V [px]', fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)

    # Avoid duplicate legend entries
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=10)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'trajectory_ellipse_overlay.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_mahalanobis_histogram(raw_df: pd.DataFrame, output_dir: str):
    """
    Plots empirical distribution of Mahalanobis distances d_h^2 against theoretical Chi-Square (2 DOF) PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    d_sq_5s = raw_df[raw_df['horizon_sec'] == 5.0]['mahalanobis_sq'].values

    # Cap outliers for histogram display
    d_sq_clipped = np.clip(d_sq_5s, 0, 15)

    n, bins, patches = plt.hist(
        d_sq_clipped, bins=30, density=True, alpha=0.6, color='#2b5c8f', edgecolor='black', label='Empirical $d_h^2$ (h=5s)'
    )

    x_pdf = np.linspace(0, 15, 200)
    y_pdf = chi2.pdf(x_pdf, df=2)
    plt.plot(x_pdf, y_pdf, 'r-', linewidth=2.5, label='Theoretical $\\chi^2_2$ PDF')

    plt.axvline(1.386, color='blue', linestyle=':', linewidth=1.5, label='50% Threshold (1.39)')
    plt.axvline(4.605, color='orange', linestyle=':', linewidth=1.5, label='90% Threshold (4.61)')
    plt.axvline(5.991, color='green', linestyle='--', linewidth=2.0, label='95% Threshold (5.99)')

    plt.title('Mahalanobis Distance $d_h^2$ Distribution vs Theoretical $\\chi^2_2$ PDF at h=5.0s', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Mahalanobis Distance Squared $d_h^2$', fontsize=12)
    plt.ylabel('Probability Density', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'mahalanobis_dist_histogram.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
