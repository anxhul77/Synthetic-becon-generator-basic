import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_ablation_acquisition_bar(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Acquisition Probability P_A [%] for Methods A, B, C, D across motion conditions with 95% Wilson CIs.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(12, 6), dpi=300)

    motion_types = summary_df['motion_type'].unique()
    methods = summary_df['strategy'].unique()
    x = np.arange(len(motion_types))
    width = 0.2

    colors = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']

    for i, m_name in enumerate(methods):
        sub = summary_df[summary_df['strategy'] == m_name]
        p_vals = sub['acquisition_probability'].values * 100.0
        err_low = np.maximum(0.0, p_vals - sub['ci_lower'].values * 100.0)
        err_high = np.maximum(0.0, sub['ci_upper'].values * 100.0 - p_vals)
        yerr = np.vstack([err_low, err_high])

        label_short = m_name.split(' — ')[1] if ' — ' in m_name else m_name
        plt.bar(x + (i - 1.5) * width, p_vals, width, yerr=yerr, label=label_short, color=colors[i], capsize=4, edgecolor='black', alpha=0.85)

    plt.title('Ablation Study: Acquisition Probability ($P_A$) Across Methods A, B, C, D', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Target Motion Condition', fontsize=12, labelpad=8)
    plt.ylabel('Acquisition Probability [%]', fontsize=12, labelpad=8)
    plt.xticks(x, [m.replace('_', ' ').title() for m in motion_types], fontsize=11)
    plt.ylim([0, 115])
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'ablation_acquisition_probability_bar.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

def plot_ablation_search_effort(summary_df: pd.DataFrame, output_dir: str):
    """
    Plots Search Path Length L_search [px] across Methods A, B, C, D.
    """
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(11, 6), dpi=300)

    motion_types = summary_df['motion_type'].unique()
    methods = summary_df['strategy'].unique()
    x = np.arange(len(motion_types))
    width = 0.2

    colors = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']

    for i, m_name in enumerate(methods):
        sub = summary_df[summary_df['strategy'] == m_name]
        path_lens = sub['mean_search_path_len_px'].values

        label_short = m_name.split(' — ')[1] if ' — ' in m_name else m_name
        plt.bar(x + (i - 1.5) * width, path_lens, width, label=label_short, color=colors[i], edgecolor='black', alpha=0.85)

    plt.title('Ablation Study: Search Path Length ($L_{\\text{search}}$) Comparison', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Target Motion Condition', fontsize=12, labelpad=8)
    plt.ylabel('Search Path Length [px]', fontsize=12, labelpad=8)
    plt.xticks(x, [m.replace('_', ' ').title() for m in motion_types], fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'ablation_search_effort_comparison.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
