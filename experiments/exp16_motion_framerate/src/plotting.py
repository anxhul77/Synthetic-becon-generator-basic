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

def plot_operational_boundary_heatmap(df_grid: pd.DataFrame, output_path: str):
    """Figure 1: 2D Heatmap of Track Maintenance Ratio (P_track) over Angular Velocity vs FPS."""
    set_style()
    pivot = df_grid.pivot(index="fps", columns="omega_deg_per_sec", values="p_track_pct")

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.matshow(pivot.values, cmap="RdYlGn", vmin=0, vmax=100)

    # Label axes
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels([f"{c:.1f}°/s" for c in pivot.columns])
    ax.set_yticklabels([f"{r:.0f} FPS" for r in pivot.index])

    ax.xaxis.set_ticks_position('bottom')
    ax.set_xlabel("Beacon Angular Velocity ω [deg/s]")
    ax.set_ylabel("Camera Frame Rate [FPS]")
    ax.set_title("Experiment 16: Tracker Operational Boundary Heatmap (P_track %)")

    # Annotate values
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            color = "black" if val > 50 else "white"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontweight="bold")

    fig.colorbar(cax, label="Track Maintenance P_track [%]")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_rmse_theta_vs_omega(df_grid: pd.DataFrame, output_path: str):
    """Figure 2: Angular RMSE pointing error vs Angular Velocity for each camera FPS."""
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    for fps_val in sorted(df_grid["fps"].unique()):
        sub = df_grid[df_grid["fps"] == fps_val].sort_values("omega_deg_per_sec")
        ax.plot(sub["omega_deg_per_sec"], sub["rmse_theta_urad"], "o--", linewidth=2.0, label=f"{fps_val:.0f} FPS")

    ax.set_xscale("log")
    ax.set_title("Experiment 16: Angular Pointing Error RMSE_θ vs Angular Velocity")
    ax.set_xlabel("Beacon Angular Velocity ω [deg/s] (Log Scale)")
    ax.set_ylabel("Angular Pointing Error RMSE_θ [μrad]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def plot_reacquisition_time_vs_omega(df_grid: pd.DataFrame, output_path: str):
    """Figure 3: Reacquisition time T_reacquire vs Angular Velocity across camera FPS."""
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    for fps_val in sorted(df_grid["fps"].unique()):
        sub = df_grid[df_grid["fps"] == fps_val].sort_values("omega_deg_per_sec")
        ax.plot(sub["omega_deg_per_sec"], sub["t_reacquire_sec"] * 1000.0, "s-", linewidth=2.0, label=f"{fps_val:.0f} FPS")

    ax.set_xscale("log")
    ax.set_title("Experiment 16: Reacquisition Time T_reacquire [ms] vs Angular Velocity")
    ax.set_xlabel("Beacon Angular Velocity ω [deg/s] (Log Scale)")
    ax.set_ylabel("Reacquisition Time T_reacquire [ms]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


def generate_all_experiment_16_plots(df_grid: pd.DataFrame, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    plot_operational_boundary_heatmap(df_grid, os.path.join(output_dir, "operational_boundary_heatmap.png"))
    plot_rmse_theta_vs_omega(df_grid, os.path.join(output_dir, "rmse_theta_vs_omega.png"))
    plot_reacquisition_time_vs_omega(df_grid, os.path.join(output_dir, "reacquisition_time_vs_omega.png"))
