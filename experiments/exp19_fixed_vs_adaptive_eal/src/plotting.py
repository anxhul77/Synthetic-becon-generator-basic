import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

def plot_fixed_vs_adaptive_trajectories(sample_trial: dict, output_dir: str):
    """
    Plots Fixed EAL vs Uncertainty-Adaptive EAL search trajectories overlaid on target trajectory and 95% uncertainty ellipse.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

    # 1. Fixed EAL Plot
    ax1.plot(sample_trial["target_u"], sample_trial["target_v"], 'k--', linewidth=2.0, label='True Target Path')
    ax1.plot(sample_trial["fixed_u"], sample_trial["fixed_v"], color='#1f77b4', linewidth=1.5, label='Fixed EAL Path')
    ax1.scatter(sample_trial["center_u"], sample_trial["center_v"], color='red', marker='x', s=100, label='Search Center')

    if sample_trial["fixed_acq_t"] is not None:
        ax1.scatter(sample_trial["fixed_acq_u"], sample_trial["fixed_acq_v"], color='green', marker='*', s=200, zorder=5, label=f'Acquired ({sample_trial["fixed_acq_t"]:.2f}s)')

    ax1.set_title('Fixed EAL Search Strategy', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Pixel U [px]', fontsize=11)
    ax1.set_ylabel('Pixel V [px]', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=9)

    # 2. Uncertainty-Adaptive EAL Plot
    ax2.plot(sample_trial["target_u"], sample_trial["target_v"], 'k--', linewidth=2.0, label='True Target Path')
    ax2.plot(sample_trial["adaptive_u"], sample_trial["adaptive_v"], color='#2ca02c', linewidth=1.5, label='Adaptive EAL Path')
    ax2.scatter(sample_trial["center_u"], sample_trial["center_v"], color='red', marker='x', s=100, label='Search Center')

    # Draw 95% Uncertainty Ellipse
    a = sample_trial["ellipse_a"]
    b = sample_trial["ellipse_b"]
    phi_deg = sample_trial["ellipse_phi_deg"]
    ellipse = Ellipse(
        xy=(sample_trial["center_u"], sample_trial["center_v"]),
        width=2*a, height=2*b, angle=phi_deg,
        edgecolor='purple', facecolor='purple', alpha=0.15, linewidth=2.0, linestyle='--', label='95% Uncertainty Ellipse'
    )
    ax2.add_patch(ellipse)

    if sample_trial["adaptive_acq_t"] is not None:
        ax2.scatter(sample_trial["adaptive_acq_u"], sample_trial["adaptive_acq_v"], color='green', marker='*', s=200, zorder=5, label=f'Acquired ({sample_trial["adaptive_acq_t"]:.2f}s)')

    ax2.set_title('Uncertainty-Adaptive EAL Search Strategy', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Pixel U [px]', fontsize=11)
    ax2.set_ylabel('Pixel V [px]', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=9)

    plt.suptitle('Fixed vs Uncertainty-Adaptive EAL Coarse Search Comparison', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'fixed_vs_adaptive_trajectories.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_acquisition_probability_bar(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Acquisition Probability P_A [%] for Fixed EAL vs Adaptive EAL across motion conditions with 95% Wilson CIs.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    motion_types = summary_df['motion_type'].unique()
    x = np.arange(len(motion_types))
    width = 0.35

    fixed_sub = summary_df[summary_df['strategy'] == 'Fixed EAL']
    adaptive_sub = summary_df[summary_df['strategy'] == 'Adaptive EAL']

    p_fixed = fixed_sub['acquisition_probability'].values * 100.0
    err_fixed_low = np.maximum(0.0, p_fixed - fixed_sub['ci_lower'].values * 100.0)
    err_fixed_high = np.maximum(0.0, fixed_sub['ci_upper'].values * 100.0 - p_fixed)
    p_fixed_err = np.vstack([err_fixed_low, err_fixed_high])

    p_adapt = adaptive_sub['acquisition_probability'].values * 100.0
    err_adapt_low = np.maximum(0.0, p_adapt - adaptive_sub['ci_lower'].values * 100.0)
    err_adapt_high = np.maximum(0.0, adaptive_sub['ci_upper'].values * 100.0 - p_adapt)
    p_adapt_err = np.vstack([err_adapt_low, err_adapt_high])

    plt.bar(x - width/2, p_fixed, width, yerr=p_fixed_err, label='Fixed EAL', color='#1f77b4', capsize=5, edgecolor='black', alpha=0.85)
    plt.bar(x + width/2, p_adapt, width, yerr=p_adapt_err, label='Adaptive EAL', color='#2ca02c', capsize=5, edgecolor='black', alpha=0.85)

    plt.title('Acquisition Probability ($P_A$) Comparison Across Motion Conditions', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Target Motion Condition', fontsize=12, labelpad=8)
    plt.ylabel('Acquisition Probability [%]', fontsize=12, labelpad=8)
    plt.xticks(x, [m.replace('_', ' ').title() for m in motion_types], fontsize=11)
    plt.ylim([0, 115])
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=11, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'acquisition_probability_bar.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_time_to_acquisition_box(raw_df: pd.DataFrame, output_dir: str):
    """
    Plots Time-to-Acquisition T_A [s] comparison between Fixed and Adaptive EAL.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(9, 6), dpi=300)

    sub_acq = raw_df[raw_df['acquired'] == True]

    strategies = ['Fixed EAL', 'Adaptive EAL']
    data = [sub_acq[sub_acq['strategy'] == s]['acq_time_sec'].values for s in strategies]

    bp = plt.boxplot(data, tick_labels=strategies, patch_artist=True, widths=0.4)

    colors = ['#1f77b4', '#2ca02c']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    plt.title('Time-to-Acquisition ($T_A$) Distribution Comparison', fontsize=14, fontweight='bold', pad=12)
    plt.ylabel('Time-to-Acquisition [seconds]', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'time_to_acquisition_box.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
