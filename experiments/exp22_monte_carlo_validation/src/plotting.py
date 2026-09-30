import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_monte_carlo_acquisition_ecdf(raw_df: pd.DataFrame, output_dir: str):
    """
    Plots Empirical Cumulative Distribution Function (ECDF) of acquisition time T_A for Methods A, B, C, D.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    methods = raw_df['strategy'].unique()
    colors = {'Method A — Fixed EAL': '#d62728',
              'Method B — Predictive Fixed EAL': '#ff7f0e',
              'Method C — Uncertainty-Adaptive EAL': '#1f77b4',
              'Method D — Full Adaptive EAL': '#2ca02c'}

    for m in methods:
        sub = raw_df[(raw_df['strategy'] == m) & (raw_df['acquired'] == True)]
        if len(sub) == 0:
            continue
        t_vals = np.sort(sub['acq_time_sec'].values)
        ecdf = np.arange(1, len(t_vals) + 1) / len(raw_df[raw_df['strategy'] == m])

        plt.step(t_vals, ecdf * 100.0, where='post', label=m.split(' — ')[1], color=colors.get(m, 'gray'), linewidth=2.0)

    plt.title('Monte Carlo ECDF: Time-to-Acquisition ($T_A$) Distribution', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Time-to-Acquisition $T_A$ [seconds]', fontsize=12, labelpad=8)
    plt.ylabel('Cumulative Acquisition Probability [%]', fontsize=12, labelpad=8)
    plt.xlim([0, 5.0])
    plt.ylim([0, 105])
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='lower right', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'monte_carlo_acquisition_cdf.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_monte_carlo_parameter_sensitivity(raw_df: pd.DataFrame, output_dir: str):
    """
    Plots acquisition success vs target acceleration and SNR.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)

    # 1. Acquisition vs Acceleration
    for m in raw_df['strategy'].unique():
        sub = raw_df[raw_df['strategy'] == m]
        acc_bins = np.linspace(0, 40, 6)
        bins_mid = 0.5 * (acc_bins[:-1] + acc_bins[1:])
        acq_rate = []
        for j in range(len(acc_bins)-1):
            mask = (sub['target_accel_px_s2'] >= acc_bins[j]) & (sub['target_accel_px_s2'] < acc_bins[j+1])
            b_sub = sub[mask]
            acq_rate.append(np.mean(b_sub['acquired']) * 100.0 if len(b_sub) > 0 else 0.0)

        label_short = m.split(' — ')[1]
        ax1.plot(bins_mid, acq_rate, marker='o', linewidth=2.0, label=label_short)

    ax1.set_title('Acquisition vs Target Acceleration ($a$)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Acceleration [px/s$^2$]', fontsize=11)
    ax1.set_ylabel('Acquisition Probability [%]', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=9)

    # 2. Acquisition vs SNR
    for m in raw_df['strategy'].unique():
        sub = raw_df[raw_df['strategy'] == m]
        snr_bins = np.linspace(5, 30, 6)
        bins_mid = 0.5 * (snr_bins[:-1] + snr_bins[1:])
        acq_rate = []
        for j in range(len(snr_bins)-1):
            mask = (sub['snr_db'] >= snr_bins[j]) & (sub['snr_db'] < snr_bins[j+1])
            b_sub = sub[mask]
            acq_rate.append(np.mean(b_sub['acquired']) * 100.0 if len(b_sub) > 0 else 0.0)

        label_short = m.split(' — ')[1]
        ax2.plot(bins_mid, acq_rate, marker='s', linewidth=2.0, label=label_short)

    ax2.set_title('Acquisition vs Link SNR', fontsize=12, fontweight='bold')
    ax2.set_xlabel('SNR [dB]', fontsize=11)
    ax2.set_ylabel('Acquisition Probability [%]', fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=9)

    plt.suptitle('Monte Carlo Parameter Sensitivity Analysis', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'monte_carlo_parameter_sensitivity.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_monte_carlo_method_comparison(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Method comparison bar chart for In-Distribution vs Stress Testing regimes.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6), dpi=300)

    regimes = summary_df['regime'].unique()
    methods = summary_df['strategy'].unique()
    x = np.arange(len(regimes))
    width = 0.2

    colors = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']

    for i, m_name in enumerate(methods):
        sub = summary_df[summary_df['strategy'] == m_name]
        p_vals = sub['acquisition_probability'].values * 100.0

        label_short = m_name.split(' — ')[1]
        plt.bar(x + (i - 1.5) * width, p_vals, width, label=label_short, color=colors[i], edgecolor='black', alpha=0.85)

    plt.title('Monte Carlo Validation: In-Distribution vs Stress Testing Regimes', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Operating Regime', fontsize=12, labelpad=8)
    plt.ylabel('Acquisition Probability [%]', fontsize=12, labelpad=8)
    plt.xticks(x, [r.replace('_', ' ').title() for r in regimes], fontsize=11)
    plt.ylim([0, 115])
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'monte_carlo_method_comparison.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
