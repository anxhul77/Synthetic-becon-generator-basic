"""
Plotting Suite for Experiment 12: Atmospheric Propagation Scenarios.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate_all_experiment_12_plots(df_summary: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('ggplot')

    # 1. Detection Probability vs Distance by Atmospheric Scenario
    fig, ax = plt.subplots(figsize=(10, 6))
    sub = df_summary[df_summary["method"] == "Gaussian Fitting"]
    for scen in sub["scenario_name"].unique():
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        ax.plot(s_df["range_km"], s_df["p_detection_pct"], marker='o', linewidth=2.0, label=scen.title())

    ax.set_title("Exp 12: Detection Probability P_D vs Propagation Distance across Scenarios", fontsize=13, fontweight='bold')
    ax.set_xlabel("Propagation Distance L [km]", fontsize=11)
    ax.set_ylabel("Detection Probability P_D [%]", fontsize=11)
    ax.set_ylim(-5, 105)
    ax.axhline(95.0, color='red', linestyle='--', label="Requirement Target (95%)")
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig01_detection_prob_vs_scenario_range.png"), dpi=300)
    plt.savefig(os.path.join(output_dir, "detection_prob_vs_distance.png"), dpi=300)
    plt.close(fig)

    # 2. Received Signal Amplitude vs Distance by Scenario
    fig, ax = plt.subplots(figsize=(10, 6))
    for scen in sub["scenario_name"].unique():
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        ax.plot(s_df["range_km"], s_df["received_amplitude_dn"], marker='s', linewidth=2.0, label=scen.title())

    ax.set_title("Exp 12: Received Peak Signal Amplitude vs Propagation Distance", fontsize=13, fontweight='bold')
    ax.set_xlabel("Propagation Distance L [km]", fontsize=11)
    ax.set_ylabel("Received Amplitude (DN)", fontsize=11)
    ax.axhline(10.5, color='black', linestyle=':', label="Detector Sensitivity Limit (10.5 DN)")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig02_received_amplitude_vs_range.png"), dpi=300)
    plt.close(fig)

    # 3. Angular Pointing Error RMSE vs Distance
    fig, ax = plt.subplots(figsize=(10, 6))
    for scen in sub["scenario_name"].unique():
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        valid_df = s_df.dropna(subset=["rmse_angular_urad"])
        if not valid_df.empty:
            ax.plot(valid_df["range_km"], valid_df["rmse_angular_urad"], marker='^', linewidth=2.0, label=scen.title())

    ax.set_title("Exp 12: Angular Pointing RMSE vs Distance across Scenarios", fontsize=13, fontweight='bold')
    ax.set_xlabel("Propagation Distance L [km]", fontsize=11)
    ax.set_ylabel("Angular Error RMSE [μrad]", fontsize=11)
    ax.axhline(100.0, color='red', linestyle='--', label="Requirement Target (100 μrad)")
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig03_angular_rmse_vs_range.png"), dpi=300)
    plt.close(fig)

    print(f"Generated Exp 12 scenario plots in: {output_dir}")
