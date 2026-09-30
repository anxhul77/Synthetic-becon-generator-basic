import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_innovation_nis_trace(sample_trial: dict, output_dir: str):
    """
    Plots real-time observable NIS_k trace and resulting search amplitude adaptation A_1, A_2.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, dpi=300)

    t_nis = sample_trial["nis_time"]
    nis_vals = sample_trial["nis_vals"]

    ax1.plot(t_nis, nis_vals, color='#d62728', linewidth=1.5, label='Observable $NIS_k$')
    ax1.axhline(5.991, color='black', linestyle='--', linewidth=1.2, label='95% Threshold (5.99)')
    ax1.set_ylabel('Normalized Innovation ($NIS_k$)', fontsize=11)
    ax1.set_title('Real-Time Observable Kalman Innovation Trace & Search Amplitude Adaptation', fontsize=13, fontweight='bold', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=10)

    t_search = sample_trial["search_time"]
    A1_vals = sample_trial["A1_trace"]
    A2_vals = sample_trial["A2_trace"]

    ax2.plot(t_search, A1_vals, color='#1f77b4', linewidth=2.0, label='Adapted $A_1(t)$ (Major Axis)')
    ax2.plot(t_search, A2_vals, color='#2ca02c', linewidth=2.0, label='Adapted $A_2(t)$ (Minor Axis)')
    ax2.axhline(sample_trial["A_max"], color='darkred', linestyle=':', label='Max Actuator Bound $A_{\\text{max}}$')

    ax2.set_xlabel('Time [seconds]', fontsize=11)
    ax2.set_ylabel('Search Amplitude [px]', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'innovation_nis_trace.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_adaptive_search_overlay(sample_trial: dict, output_dir: str):
    """
    Plots search paths for Uncertainty-Only EAL vs Error-Adaptive EAL under maneuvering target.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

    ax1.plot(sample_trial["target_u"], sample_trial["target_v"], 'k--', linewidth=2.0, label='Target Path')
    ax1.plot(sample_trial["u_unc"], sample_trial["v_unc"], color='#1f77b4', linewidth=1.5, label='Uncertainty-Only EAL')
    ax1.scatter(sample_trial["cx"], sample_trial["cy"], color='red', marker='x', s=100, label='Center')
    ax1.set_title('Uncertainty-Only EAL (No Residual Adapt)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Pixel U [px]', fontsize=11)
    ax1.set_ylabel('Pixel V [px]', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=9)

    ax2.plot(sample_trial["target_u"], sample_trial["target_v"], 'k--', linewidth=2.0, label='Target Path')
    ax2.plot(sample_trial["u_err"], sample_trial["v_err"], color='#2ca02c', linewidth=1.5, label='Error-Adaptive EAL')
    ax2.scatter(sample_trial["cx"], sample_trial["cy"], color='red', marker='x', s=100, label='Center')

    if sample_trial["acq_t_err"] is not None:
        ax2.scatter(sample_trial["acq_u_err"], sample_trial["acq_v_err"], color='green', marker='*', s=200, zorder=5, label=f'Acquired ({sample_trial["acq_t_err"]:.2f}s)')

    ax2.set_title('Error-Adaptive EAL (Innovation Feedback)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Pixel U [px]', fontsize=11)
    ax2.set_ylabel('Pixel V [px]', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=9)

    plt.suptitle('Prediction-Error Adaptation under Target Maneuver', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'adaptive_search_overlay.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_acquisition_performance_comparison(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Acquisition Probability P_A [%] across search strategies and motion conditions.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    motion_types = summary_df['motion_type'].unique()
    x = np.arange(len(motion_types))
    width = 0.35

    unc_sub = summary_df[summary_df['strategy'] == 'Uncertainty-Only EAL']
    err_sub = summary_df[summary_df['strategy'] == 'Error-Adaptive EAL']

    p_unc = unc_sub['acquisition_probability'].values * 100.0
    err_unc_low = np.maximum(0.0, p_unc - unc_sub['ci_lower'].values * 100.0)
    err_unc_high = np.maximum(0.0, unc_sub['ci_upper'].values * 100.0 - p_unc)
    yerr_unc = np.vstack([err_unc_low, err_unc_high])

    p_err = err_sub['acquisition_probability'].values * 100.0
    err_err_low = np.maximum(0.0, p_err - err_sub['ci_lower'].values * 100.0)
    err_err_high = np.maximum(0.0, err_sub['ci_upper'].values * 100.0 - p_err)
    yerr_err = np.vstack([err_err_low, err_err_high])

    plt.bar(x - width/2, p_unc, width, yerr=yerr_unc, label='Uncertainty-Only EAL', color='#1f77b4', capsize=5, edgecolor='black', alpha=0.85)
    plt.bar(x + width/2, p_err, width, yerr=yerr_err, label='Error-Adaptive EAL', color='#2ca02c', capsize=5, edgecolor='black', alpha=0.85)

    plt.title('Acquisition Probability ($P_A$) with Prediction-Error Adaptation', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Target Motion Condition', fontsize=12, labelpad=8)
    plt.ylabel('Acquisition Probability [%]', fontsize=12, labelpad=8)
    plt.xticks(x, [m.replace('_', ' ').title() for m in motion_types], fontsize=11)
    plt.ylim([0, 115])
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=11, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'acquisition_performance_comparison.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
