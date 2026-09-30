import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def set_style():
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 15,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 11,
        'figure.titlesize': 16,
        'figure.dpi': 300
    })

def plot_geometric_and_optical_power(df_summary: pd.DataFrame, output_dir: str):
    """Figures 1-2: Geometric & Optical Link Power vs Range."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    # 1. Received Amplitude & Beam Radius vs Distance
    fig, ax1 = plt.subplots(figsize=(10, 6))
    sub = df_summary[df_summary["sub_exp_id"] == "13B_optical_power"].sort_values("range_km")
    if sub.empty:
        sub = df_summary.sort_values("range_km")

    color = 'tab:blue'
    ax1.set_xlabel('Propagation Distance L [km]')
    ax1.set_ylabel('Received Amplitude [DN]', color=color)
    ax1.plot(sub["range_km"], sub["received_amplitude"], color=color, marker='o', linewidth=2.5, label="Received Amplitude")
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Beam Radius w(L) [m]', color=color)
    ax2.plot(sub["range_km"], sub["beam_radius_m"], color=color, marker='s', linestyle='--', linewidth=2.0, label="Beam Radius w(L)")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("Stage 13B: Received Optical Signal & Beam Spreading vs Distance")
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, "optical_power_vs_distance.png"), bbox_inches='tight', dpi=300)
    plt.close()


def plot_detection_prob_and_rmse(df_summary: pd.DataFrame, output_dir: str):
    """Figures 3-4: Detection Probability P_D and Angular RMSE vs Range across estimators."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    sub = df_summary[df_summary["sub_exp_id"] == "13E_combined"]
    if sub.empty:
        sub = df_summary

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for method in sub["method"].unique():
        s_m = sub[sub["method"] == method].sort_values("range_km")
        ax1.plot(s_m["range_km"], s_m["p_detection_pct"], marker='o', linewidth=2.0, label=method)
        ax2.plot(s_m["range_km"], s_m["rmse_angular_urad"], marker='s', linewidth=2.0, label=method)

    ax1.axhline(95.0, color="red", linestyle="--", alpha=0.7, label="Min Req (95%)")
    ax1.set_title("Stage 13E: Detection Probability P_D vs Range")
    ax1.set_xlabel("Propagation Distance L [km]")
    ax1.set_ylabel("Detection Probability P_D [%]")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="lower left")
    ax1.grid(True, alpha=0.3)

    ax2.axhline(100.0, color="red", linestyle="--", alpha=0.7, label="Max Req (100 μrad)")
    ax2.set_title("Stage 13E: Angular Pointing RMSE vs Range")
    ax2.set_xlabel("Propagation Distance L [km]")
    ax2.set_ylabel("Angular Error RMSE [μrad]")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "detection_rmse_vs_range.png"), bbox_inches='tight', dpi=300)
    plt.close()


def plot_operating_envelope(df_summary: pd.DataFrame, output_dir: str):
    """Figure 5: Operating Envelope Compliance Chart."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    sub = df_summary[(df_summary["sub_exp_id"] == "13E_combined") & (df_summary["method"] == "Gaussian Fitting")].sort_values("range_km")
    if sub.empty:
        sub = df_summary[df_summary["method"] == "Gaussian Fitting"].sort_values("range_km")

    fig, ax = plt.subplots(figsize=(10, 6))

    distances = sub["range_km"].values
    compliances = sub["is_fully_compliant"].values
    colors = ["green" if c else "red" for c in compliances]
    labels = ["Compliant" if c else "Non-Compliant" for c in compliances]

    bars = ax.bar([f"{d:.1f} km" for d in distances], sub["p_detection_pct"], color=colors, alpha=0.85, edgecolor="black")

    ax.axhline(95.0, color="darkred", linestyle="--", linewidth=2.0, label="95% P_D Requirement")
    ax.set_title("Experiment 13: Tracker Operating Envelope Compliance")
    ax.set_xlabel("Propagation Range L [km]")
    ax.set_ylabel("Detection Probability P_D [%]")
    ax.set_ylim(0, 110)

    for bar, c_flag in zip(bars, compliances):
        yval = bar.get_height()
        status_str = "✓ PASSED" if c_flag else "✗ FAILED"
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2.0, status_str, ha='center', va='bottom', fontweight='bold', color="darkgreen" if c_flag else "darkred")

    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "operating_envelope_compliance.png"), bbox_inches='tight', dpi=300)
    plt.close()


def generate_all_experiment_13_plots(df_summary: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plot_geometric_and_optical_power(df_summary, output_dir)
    plot_detection_prob_and_rmse(df_summary, output_dir)
    plot_operating_envelope(df_summary, output_dir)
