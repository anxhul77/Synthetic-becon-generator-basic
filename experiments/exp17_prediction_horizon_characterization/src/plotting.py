import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_exp17_figures(df_raw: pd.DataFrame, df_summary: pd.DataFrame, output_dir: str):
    """
    Generates all 6 required diagnostic plots for Experiment 17:
      - Fig 1: Prediction RMSE vs Horizon
      - Fig 2: Empirical Prediction-Error Standard Deviation vs Horizon
      - Fig 3: Predicted Covariance Standard Deviation vs Horizon
      - Fig 4: Example True vs Predicted Trajectories
      - Fig 5: Error Distributions at Each Horizon
      - Fig 6: Angular Prediction Error vs Horizon
    """
    os.makedirs(output_dir, exist_ok=True)
    horizons = sorted(df_summary["horizon_sec"].unique())
    motion_types = df_raw["motion_type"].unique()

    color_map = {
        "linear_cv": "#1f77b4",
        "maneuvering_circular": "#ff7f0e",
        "random_walk_accel": "#2ca02c"
    }

    # -------------------------------------------------------------------------
    # Fig 01: Prediction RMSE vs Horizon
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    for m in motion_types:
        sub_m = df_raw[df_raw["motion_type"] == m]
        rmse_vals = [np.sqrt(np.mean(sub_m[sub_m["horizon_sec"] == h]["radial_error_px"] ** 2)) for h in horizons]
        plt.plot(horizons, rmse_vals, marker="o", linewidth=2.0, color=color_map.get(m, "blue"), label=f"{m} (Empirical)")

    # Overall RMSE
    overall_rmse = [np.sqrt(np.mean(df_raw[df_raw["horizon_sec"] == h]["radial_error_px"] ** 2)) for h in horizons]
    plt.plot(horizons, overall_rmse, marker="s", linewidth=2.5, color="black", linestyle="--", label="Overall RMSE")

    plt.title("Figure 1: Position Prediction RMSE vs. Horizon h")
    plt.xlabel("Prediction Horizon h (seconds)")
    plt.ylabel("Position RMSE (pixels)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig01_prediction_rmse_vs_horizon.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # Fig 02: Empirical Prediction-Error Standard Deviation vs Horizon
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    for m in motion_types:
        sub_m = df_raw[df_raw["motion_type"] == m]
        std_vals = [np.std(sub_m[sub_m["horizon_sec"] == h]["radial_error_px"]) for h in horizons]
        plt.plot(horizons, std_vals, marker="^", linewidth=2.0, color=color_map.get(m, "blue"), label=f"{m} Std Dev")

    overall_std = [np.std(df_raw[df_raw["horizon_sec"] == h]["radial_error_px"]) for h in horizons]
    plt.plot(horizons, overall_std, marker="D", linewidth=2.5, color="purple", linestyle=":", label="Overall Empirical Std")

    plt.title("Figure 2: Empirical Prediction-Error Standard Deviation vs. Horizon")
    plt.xlabel("Prediction Horizon h (seconds)")
    plt.ylabel("Empirical Error Std Dev (pixels)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig02_empirical_std_vs_horizon.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # Fig 03: Predicted Covariance Standard Deviation vs Horizon
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    pred_sigma_u = [np.mean(df_raw[df_raw["horizon_sec"] == h]["sigma_u_pred"]) for h in horizons]
    pred_sigma_v = [np.mean(df_raw[df_raw["horizon_sec"] == h]["sigma_v_pred"]) for h in horizons]

    plt.plot(horizons, pred_sigma_u, marker="s", linewidth=2.0, color="#d62728", label=r"Predicted $\sigma_u(h) = \sqrt{P_{uu}}$")
    plt.plot(horizons, pred_sigma_v, marker="o", linewidth=2.0, color="#17becf", label=r"Predicted $\sigma_v(h) = \sqrt{P_{vv}}$")

    # Comparison against empirical std
    plt.plot(horizons, overall_std, marker="x", linewidth=1.8, color="black", linestyle="--", label="Empirical Error Std")

    plt.title("Figure 3: Predicted Covariance Standard Deviation vs. Horizon")
    plt.xlabel("Prediction Horizon h (seconds)")
    plt.ylabel("Standard Deviation (pixels)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig03_predicted_covariance_std_vs_horizon.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # Fig 04: Example True vs Predicted Trajectories
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 6))
    sub_cv = df_raw[df_raw["motion_type"] == "linear_cv"].iloc[:30]
    if len(sub_cv) > 0:
        plt.plot(sub_cv["gt_x_future"], sub_cv["gt_y_future"], "k-o", label="Ground Truth Trajectory", markersize=4)
        plt.scatter(sub_cv["pred_x"], sub_cv["pred_y"], c=sub_cv["horizon_sec"], cmap="viridis", label="Predicted Points", zorder=5)
        cbar = plt.colorbar()
        cbar.set_label("Horizon h (seconds)")

    plt.title("Figure 4: Example True vs. Predicted Beacon Trajectories")
    plt.xlabel("Position X (pixels)")
    plt.ylabel("Position Y (pixels)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig04_true_vs_predicted_trajectories.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # Fig 05: Error Distributions at Each Horizon
    # -------------------------------------------------------------------------
    plt.figure(figsize=(9, 5))
    data_by_h = [df_raw[df_raw["horizon_sec"] == h]["radial_error_px"].values for h in horizons]
    plt.boxplot(data_by_h, tick_labels=[f"{h}s" for h in horizons], patch_artist=True,
                boxprops=dict(facecolor="#1f77b4", alpha=0.6))

    plt.title("Figure 5: Prediction Error Distributions across Horizons")
    plt.xlabel("Prediction Horizon h")
    plt.ylabel("Position Prediction Error (pixels)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig05_error_distributions_per_horizon.png"), dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # Fig 06: Angular Prediction Error vs Horizon
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5))
    f_px = 2000.0
    for m in motion_types:
        sub_m = df_raw[df_raw["motion_type"] == m]
        ang_rmse_mrad = [np.sqrt(np.mean((np.arctan(sub_m[sub_m["horizon_sec"] == h]["radial_error_px"] / f_px) * 1000.0) ** 2)) for h in horizons]
        plt.plot(horizons, ang_rmse_mrad, marker="p", linewidth=2.0, color=color_map.get(m, "blue"), label=f"{m} (mrad)")

    overall_ang_mrad = [np.sqrt(np.mean((np.arctan(df_raw[df_raw["horizon_sec"] == h]["radial_error_px"] / f_px) * 1000.0) ** 2)) for h in horizons]
    plt.plot(horizons, overall_ang_mrad, marker="*", linewidth=2.5, color="darkred", linestyle="--", label="Overall Angular RMSE")

    plt.title("Figure 6: Angular Prediction Error vs. Horizon (f = 2000 px)")
    plt.xlabel("Prediction Horizon h (seconds)")
    plt.ylabel("Angular Prediction RMSE (mrad)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig06_angular_prediction_error_vs_horizon.png"), dpi=300)
    plt.close()
