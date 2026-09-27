import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator

def run_snr_calibration():
    print("====================================================")
    print("RUNNING DETAILED SNR CALIBRATION & AUDIT SUITE")
    print("====================================================\n")

    results_dir = "results/exp00"
    figures_dir = "reports/figures"
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    camera = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0, fps=60.0)
    generator = SyntheticBeaconGenerator(camera=camera)

    snr_levels = [0.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
    amplitude = 150.0
    background_level = 10.0
    seed_base = 9999

    rows = []

    for idx, snr_cfg in enumerate(snr_levels):
        seed = seed_base + idx
        # Calculate configured noise sigma
        sigma_configured = amplitude * (10.0 ** (-snr_cfg / 20.0))

        # Generate frame in float64 without clipping to measure true raw noise statistics
        rng = np.random.default_rng(seed)
        noise_raw = rng.normal(0.0, sigma_configured, size=(1080, 1920))
        measured_sigma_raw = float(np.std(noise_raw))
        measured_snr_raw = 20.0 * np.log10(amplitude / measured_sigma_raw)
        diff_raw = abs(measured_snr_raw - snr_cfg)

        # Generate frame through full camera pipeline with sensor clipping (uint8 & float64)
        img_sensor, gt = generator.generate_frame(
            x0=960.0, y0=540.0, amplitude=amplitude, sigma_x=2.0, sigma_y=2.0,
            snr_db=snr_cfg, background_level=background_level, bit_depth=64, seed=seed
        )

        # Measure noise std from background corner away from beacon
        bg_corner = img_sensor[0:100, 0:100]
        measured_sigma_sensor = float(np.std(bg_corner))

        # Peak signal measurement
        peak_measured = float(np.max(img_sensor)) - float(np.mean(bg_corner))
        measured_snr_sensor = 20.0 * np.log10(amplitude / measured_sigma_sensor) if measured_sigma_sensor > 0 else 100.0
        diff_sensor = abs(measured_snr_sensor - snr_cfg)

        rows.append({
            "configured_snr_db": snr_cfg,
            "noise_sigma_configured": sigma_configured,
            "measured_noise_sigma_raw": measured_sigma_raw,
            "measured_snr_raw_db": measured_snr_raw,
            "diff_raw_db": diff_raw,
            "measured_noise_sigma_sensor": measured_sigma_sensor,
            "measured_snr_sensor_db": measured_snr_sensor,
            "diff_sensor_db": diff_sensor
        })

        print(f"Config SNR: {snr_cfg:4.1f} dB | Sig Config: {sigma_configured:8.4f} | Raw Sig Msr: {measured_sigma_raw:8.4f} | Raw SNR Msr: {measured_snr_raw:5.2f} dB | Sensor SNR Msr: {measured_snr_sensor:5.2f} dB")

    df = pd.DataFrame(rows)
    csv_path = os.path.join(results_dir, "snr_calibration.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved calibration data to: {csv_path}")

    # Generate Plot: Configured vs Measured SNR
    fig, ax = plt.subplots(figsize=(9, 6))
    cfgs = df["configured_snr_db"].values
    snr_raw = df["measured_snr_raw_db"].values
    snr_sns = df["measured_snr_sensor_db"].values

    ax.plot(cfgs, cfgs, 'k--', lw=2, label="Ideal Calibration Line (1:1)")
    ax.plot(cfgs, snr_raw, 'go-', lw=2, ms=8, label="Measured Raw Unclipped Noise SNR")
    ax.plot(cfgs, snr_sns, 'ro--', lw=2, ms=8, label="Measured Sensor Clipped Image SNR")

    ax.set_title("FSOC Beacon Generator SNR Calibration Curve")
    ax.set_xlabel("Configured SNR (dB)")
    ax.set_ylabel("Measured SNR (dB)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    plot_path = os.path.join(figures_dir, "snr_calibration.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved SNR calibration figure to: {plot_path}")

    return df

if __name__ == "__main__":
    run_snr_calibration()
