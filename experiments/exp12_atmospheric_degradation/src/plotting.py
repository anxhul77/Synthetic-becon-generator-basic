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

def plot_distance_attenuation_metrics(df_12a: pd.DataFrame, output_dir: str):
    """Figures 1-3: Distance-dependent transmittance, amplitude, detection probability P_D, and RMSE."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    # 1. Transmittance & Amplitude vs Distance
    fig, ax1 = plt.subplots(figsize=(10, 6))
    sub = df_12a[df_12a["method"] == "Gaussian Fitting"].sort_values("range_km")

    color = 'tab:blue'
    ax1.set_xlabel('Propagation Distance L [km]')
    ax1.set_ylabel('Transmittance T(L)', color=color)
    ax1.plot(sub["range_km"], sub["transmittance"], color=color, marker='o', linewidth=2.5, label="Transmittance T(L)")
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Received Peak Amplitude A [DN]', color=color)
    ax2.plot(sub["range_km"], sub["received_amplitude"], color=color, marker='s', linestyle='--', linewidth=2.0, label="Received Amplitude")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("Stage 12A: Transmittance & Received Amplitude vs Distance")
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, "transmittance_amplitude_vs_distance.png"), bbox_inches='tight', dpi=300)
    plt.close()

    # 2. Detection Probability P_D vs Distance
    fig, ax = plt.subplots(figsize=(10, 6))
    for method in df_12a["method"].unique():
        s_m = df_12a[df_12a["method"] == method].sort_values("range_km")
        ax.plot(s_m["range_km"], s_m["p_detection_pct"], marker='o', linewidth=2.0, label=method)

    ax.set_title("Stage 12A: Beacon Detection Probability P_D vs Propagation Distance")
    ax.set_xlabel("Propagation Distance L [km]")
    ax.set_ylabel("Detection Probability P_D [%]")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "detection_prob_vs_distance.png"), bbox_inches='tight', dpi=300)
    plt.close()

    # 3. Localization RMSE vs Distance
    fig, ax = plt.subplots(figsize=(10, 6))
    for method in df_12a["method"].unique():
        s_m = df_12a[df_12a["method"] == method].sort_values("range_km")
        ax.plot(s_m["range_km"], s_m["rmse_pos_px"], marker='s', linewidth=2.0, label=method)

    ax.set_title("Stage 12A: Localization RMSE vs Propagation Distance")
    ax.set_xlabel("Propagation Distance L [km]")
    ax.set_ylabel("Localization RMSE [px]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rmse_vs_distance.png"), bbox_inches='tight', dpi=300)
    plt.close()


def plot_attenuation_sensitivity(df_12b: pd.DataFrame, output_dir: str):
    """Figures 4-5: Attenuation Sensitivity (P_D and RMSE vs alpha)."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    sub = df_12b[df_12b["method"] == "Gaussian Fitting"]

    for d_km in sorted(sub["range_km"].unique()):
        s_d = sub[sub["range_km"] == d_km].sort_values("attenuation_alpha")
        ax1.plot(s_d["attenuation_alpha"], s_d["p_detection_pct"], marker='o', label=f"Distance {d_km:.0f} km")
        ax2.plot(s_d["attenuation_alpha"], s_d["rmse_pos_px"], marker='s', label=f"Distance {d_km:.0f} km")

    ax1.set_title("Stage 12B: Detection Probability vs Attenuation α")
    ax1.set_xlabel("Attenuation Coefficient α [km⁻¹]")
    ax1.set_ylabel("P_D [%]")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Stage 12B: Localization RMSE vs Attenuation α")
    ax2.set_xlabel("Attenuation Coefficient α [km⁻¹]")
    ax2.set_ylabel("Localization RMSE [px]")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "attenuation_sensitivity.png"), bbox_inches='tight', dpi=300)
    plt.close()


def plot_turbulence_metrics(df_12c: pd.DataFrame, output_dir: str):
    """Figures 6-7: Turbulence Degradation (P_D, RMSE, and Angular Error vs Turbulence Strength)."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for method in df_12c["method"].unique():
        s_m = df_12c[df_12c["method"] == method].sort_values("turbulence_strength")
        ax1.plot(s_m["turbulence_strength"], s_m["p_detection_pct"], marker='o', label=method)
        ax2.plot(s_m["turbulence_strength"], s_m["rmse_angular_urad"], marker='s', label=method)

    ax1.set_title("Stage 12C: Detection Probability vs Turbulence Strength")
    ax1.set_xlabel("Normalized Turbulence Strength")
    ax1.set_ylabel("P_D [%]")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Stage 12C: Angular Pointing RMSE vs Turbulence Strength")
    ax2.set_xlabel("Normalized Turbulence Strength")
    ax2.set_ylabel("Angular Error RMSE [μrad]")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "turbulence_degradation.png"), bbox_inches='tight', dpi=300)
    plt.close()


def plot_scattering_metrics(df_12d: pd.DataFrame, output_dir: str):
    """Figures 8-9: Scattering Energy Redistribution (P_D and RMSE vs Scattering Fraction)."""
    set_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    sub = df_12d[df_12d["method"] == "Gaussian Fitting"]

    for h_sig in sorted(sub["halo_sigma"].unique()):
        s_h = sub[sub["halo_sigma"] == h_sig].sort_values("scattering_fraction")
        ax1.plot(s_h["scattering_fraction"], s_h["p_detection_pct"], marker='o', label=f"Halo σ = {h_sig:.0f} px")
        ax2.plot(s_h["scattering_fraction"], s_h["rmse_pos_px"], marker='s', label=f"Halo σ = {h_sig:.0f} px")

    ax1.set_title("Stage 12D: Detection Probability vs Scattering Fraction")
    ax1.set_xlabel("Scattering Fraction η")
    ax1.set_ylabel("P_D [%]")
    ax1.set_ylim(0, 105)
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Stage 12D: Localization RMSE vs Scattering Fraction")
    ax2.set_xlabel("Scattering Fraction η")
    ax2.set_ylabel("Localization RMSE [px]")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "scattering_degradation.png"), bbox_inches='tight', dpi=300)
    plt.close()


def generate_all_experiment_12_plots(df_summary: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    df_12a = df_summary[df_summary["sub_exp_id"] == "12A_distance"]
    if not df_12a.empty:
        plot_distance_attenuation_metrics(df_12a, output_dir)

    df_12b = df_summary[df_summary["sub_exp_id"] == "12B_attenuation"]
    if not df_12b.empty:
        plot_attenuation_sensitivity(df_12b, output_dir)

    df_12c = df_summary[df_summary["sub_exp_id"] == "12C_turbulence"]
    if not df_12c.empty:
        plot_turbulence_metrics(df_12c, output_dir)

    df_12d = df_summary[df_summary["sub_exp_id"] == "12D_scattering"]
    if not df_12d.empty:
        plot_scattering_metrics(df_12d, output_dir)
