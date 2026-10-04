"""
Plotting Suite for Experiment 13: Beacon Range and Traceable Operating Envelope.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate_all_experiment_13_plots(df_summary: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('ggplot')

    # 1. Received Amplitude vs Distance across Atmospheric Scenarios
    fig, ax = plt.subplots(figsize=(10, 6))
    sub = df_summary[df_summary["method"] == "Gaussian Fitting"]
    for scen in sub["scenario_name"].unique():
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        ax.plot(s_df["range_km"], s_df["received_amplitude_dn"], marker='o', linewidth=2.0, label=scen.title())

    ax.set_title("Exp 13: Traceable Received Signal Amplitude (DN) vs Range", fontsize=13, fontweight='bold')
    ax.set_xlabel("Propagation Range L [km]", fontsize=11)
    ax.set_ylabel("Received Amplitude (DN)", fontsize=11)
    ax.axhline(10.5, color='black', linestyle=':', label="Detector Sensitivity Limit (10.5 DN)")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "optical_power_vs_distance.png"), dpi=300)
    plt.close(fig)

    # 2. Detection Probability P_D vs Range across Scenarios
    fig, ax = plt.subplots(figsize=(10, 6))
    for scen in sub["scenario_name"].unique():
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        ax.plot(s_df["range_km"], s_df["p_detection_pct"], marker='s', linewidth=2.0, label=scen.title())

    ax.set_title("Exp 13: Detection Probability P_D vs Propagation Range", fontsize=13, fontweight='bold')
    ax.set_xlabel("Propagation Range L [km]", fontsize=11)
    ax.set_ylabel("Detection Probability P_D [%]", fontsize=11)
    ax.set_ylim(-5, 105)
    ax.axhline(95.0, color='red', linestyle='--', label="Requirement Target (95%)")
    ax.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "detection_rmse_vs_range.png"), dpi=300)
    plt.close(fig)

    # 3. Operating Envelope Compliance Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    scens = sub["scenario_name"].unique()
    x = np.arange(len(scens))
    max_comp_ranges = []
    for scen in scens:
        s_df = sub[sub["scenario_name"] == scen].sort_values("range_km")
        comp = s_df[s_df["is_fully_compliant"]]["range_km"].values
        max_c = max(comp) if len(comp) > 0 else 0.0
        max_comp_ranges.append(max_c)

    bars = ax.bar(x, max_comp_ranges, color='steelblue', edgecolor='black', alpha=0.85)
    ax.set_title("Exp 13: Compliant Operating Range Limit (L_max) per Atmospheric Scenario", fontsize=13, fontweight='bold')
    ax.set_xlabel("Atmospheric Scenario", fontsize=11)
    ax.set_ylabel("Maximum Compliant Propagation Range (km)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([s.title() for s in scens], rotation=15)

    for bar, val in zip(bars, max_comp_ranges):
        yval = bar.get_height()
        txt = f"{val:.1f} km" if val > 0 else "Non-Compliant"
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, txt, ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "operating_envelope_compliance.png"), dpi=300)
    plt.close(fig)

    print(f"Generated Exp 13 range plots in: {output_dir}")
