"""
Automated Generator Validation Reporting System.
Executes analytical, statistical, and empirical validation tests on the synthetic beacon generator
and outputs validation_report.json, validation_report.csv, and validation_summary.txt.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator.camera import PinholeCamera
from generator.psf import GaussianPSF, EllipticalGaussianPSF
from generator.background import UniformBackground, GradientBackground
from generator.atmosphere import AtmosphericModel
from generator.noise import GaussianNoise
from generator.generator import SyntheticBeaconGenerator


class ValidationRunner:
    def __init__(self, output_dir: str = "validation_results"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []

    def record_test(self, test_name: str, status: str, measured_value: float,
                    expected_value: float, error: float, tolerance: float, seed: int = None):
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "test_name": test_name,
            "status": status,
            "measured_value": float(measured_value),
            "expected_value": float(expected_value),
            "error": float(error),
            "tolerance": float(tolerance),
            "timestamp": timestamp,
            "seed": seed if seed is not None else 0
        }
        self.results.append(entry)
        status_symbol = "PASS" if status == "PASS" else "FAIL"
        print(f"[{status_symbol}] {test_name}: Measured={measured_value:.6e}, Expected={expected_value:.6e}, Error={error:.6e} (Tol={tolerance:.6e})")

    def run_camera_tests(self):
        cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
        
        # 1. Center angle
        tx, ty = cam.pixel_to_angle(960.0, 540.0)
        err = max(abs(tx), abs(ty))
        tol = 1e-10
        self.record_test("camera_center_angle", "PASS" if err <= tol else "FAIL", 0.0, 0.0, err, tol)

        # 2. Round trip error
        test_points = [(0.0, 0.0), (960.0, 540.0), (1919.0, 1079.0), (100.0, 700.0), (1500.0, 300.0)]
        max_rt_err = 0.0
        for u, v in test_points:
            t_x, t_y = cam.pixel_to_angle(u, v)
            u_rec, v_rec = cam.angle_to_pixel(t_x, t_y)
            max_rt_err = max(max_rt_err, abs(u - u_rec), abs(v - v_rec))
        tol = 1e-10
        self.record_test("camera_pixel_angle_roundtrip", "PASS" if max_rt_err <= tol else "FAIL", max_rt_err, 0.0, max_rt_err, tol)

        # 3. FOV calculation
        fov_x_exp = 2.0 * np.degrees(np.arctan(1920.0 / 4000.0))
        err_fov = abs(cam.fov_x_deg - fov_x_exp)
        tol = 1e-6
        self.record_test("camera_fov_x_equation", "PASS" if err_fov <= tol else "FAIL", cam.fov_x_deg, fov_x_exp, err_fov, tol)

    def run_psf_tests(self):
        psf = GaussianPSF(sigma_x=2.0, sigma_y=2.0)
        x = np.array([[960.0]])
        y = np.array([[540.0]])
        val = psf.render(x, y, 960.0, 540.0, 150.0)[0, 0]
        err = abs(val - 150.0)
        tol = 1e-10
        self.record_test("psf_gaussian_peak", "PASS" if err <= tol else "FAIL", val, 150.0, err, tol)

        # 1-sigma response
        x_sig = np.array([[962.0]])
        val_sig = psf.render(x_sig, y, 960.0, 540.0, 150.0)[0, 0]
        exp_sig = 150.0 * np.exp(-0.5)
        err_sig = abs(val_sig - exp_sig)
        self.record_test("psf_gaussian_one_sigma", "PASS" if err_sig <= tol else "FAIL", val_sig, exp_sig, err_sig, tol)

    def run_background_tests(self):
        bg = UniformBackground(baseline=10.0).render(100, 100)
        err = float(np.max(np.abs(bg - 10.0)))
        tol = 1e-10
        self.record_test("background_uniform_baseline", "PASS" if err <= tol else "FAIL", float(np.mean(bg)), 10.0, err, tol)

        # Gradient analytical check
        gbg = GradientBackground(baseline=10.0, a=0.01, b=0.02).render(100, 100)
        exp_corner = 10.0 + 0.01 * 99 + 0.02 * 99
        msr_corner = gbg[99, 99]
        err_grad = abs(msr_corner - exp_corner)
        self.record_test("background_gradient_corner", "PASS" if err_grad <= tol else "FAIL", msr_corner, exp_corner, err_grad, tol)

    def run_atmosphere_tests(self):
        atmo = AtmosphericModel(attenuation_alpha=0.0001, range_km=5.0)
        msr_t = atmo.calculate_transmittance()
        exp_t = np.exp(-0.0001 * 5.0)
        err = abs(msr_t - exp_t)
        tol = 1e-10
        self.record_test("atmosphere_transmittance_beer_lambert", "PASS" if err <= tol else "FAIL", msr_t, exp_t, err, tol)

    def run_noise_tests(self):
        A = 150.0
        snr_db = 30.0
        nm = GaussianNoise(snr_db=snr_db, amplitude=A)
        exp_sigma = A * (10.0 ** (-30.0 / 20.0))
        err_sig = abs(nm.sigma_n - exp_sigma)
        tol = 1e-10
        self.record_test("noise_sigma_equation", "PASS" if err_sig <= tol else "FAIL", nm.sigma_n, exp_sigma, err_sig, tol)

        # Statistical test
        seed = 42
        rng = np.random.default_rng(seed)
        dummy = np.zeros((1000, 1000), dtype=np.float64)
        noisy, _ = nm.add_noise(dummy, rng)
        msr_mean = float(np.mean(noisy))
        msr_std = float(np.std(noisy))
        err_mean = abs(msr_mean)
        err_std = abs(msr_std - exp_sigma)
        self.record_test("noise_statistical_mean", "PASS" if err_mean < 0.05 else "FAIL", msr_mean, 0.0, err_mean, 0.05, seed=seed)
        self.record_test("noise_statistical_std", "PASS" if err_std < 0.05 * exp_sigma else "FAIL", msr_std, exp_sigma, err_std, 0.05 * exp_sigma, seed=seed)

    def run_reproducibility_tests(self):
        gen = SyntheticBeaconGenerator()
        seed = 12345
        img1, gt1 = gen.generate_frame(seed=seed)
        img2, gt2 = gen.generate_frame(seed=seed)
        diff = float(np.max(np.abs(img1.astype(float) - img2.astype(float))))
        tol = 0.0
        self.record_test("reproducibility_identical_seed", "PASS" if diff == 0.0 else "FAIL", diff, 0.0, diff, tol, seed=seed)

    def run_ground_truth_tests(self):
        cam = PinholeCamera()
        gen = SyntheticBeaconGenerator(camera=cam)
        x_req, y_req = 923.37, 511.82
        _, gt = gen.generate_frame(x0=x_req, y0=y_req, seed=42)
        err_x = abs(gt["x_true"] - x_req)
        tol = 1e-10
        self.record_test("ground_truth_subpixel_x", "PASS" if err_x <= tol else "FAIL", gt["x_true"], x_req, err_x, tol, seed=42)

        exp_tx = float(np.arctan((x_req - cam.cx) / cam.fx))
        err_tx = abs(gt["theta_x_true"] - exp_tx)
        self.record_test("ground_truth_theta_x_analytical", "PASS" if err_tx <= tol else "FAIL", gt["theta_x_true"], exp_tx, err_tx, tol, seed=42)

    def save_reports(self):
        df = pd.DataFrame(self.results)
        
        # 1. Save JSON report
        json_path = os.path.join(self.output_dir, "validation_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
            
        # 2. Save CSV report
        csv_path = os.path.join(self.output_dir, "validation_report.csv")
        df.to_csv(csv_path, index=False)
        
        # 3. Save Summary Text
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        summary_lines = [
            "==================================================",
            "SYNTHETIC OPTICAL BEACON GENERATOR VALIDATION SUMMARY",
            "==================================================",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"Total Validation Tests Executed: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Overall Status: {'PASSED' if failed_tests == 0 else 'FAILED'}",
            "--------------------------------------------------",
            "TEST RESULTS SUMMARY:"
        ]
        
        for r in self.results:
            summary_lines.append(f"  - {r['test_name']:35s} [{r['status']}] (Error: {r['error']:.4e}, Tol: {r['tolerance']:.4e})")
            
        summary_txt = "\n".join(summary_lines)
        summary_path = os.path.join(self.output_dir, "validation_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_txt)
            
        print("\n" + summary_txt)
        print(f"\nValidation reports saved to: {os.path.abspath(self.output_dir)}")

    def run_all(self):
        print("Starting Automated Validation Suite...")
        self.run_camera_tests()
        self.run_psf_tests()
        self.run_background_tests()
        self.run_atmosphere_tests()
        self.run_noise_tests()
        self.run_reproducibility_tests()
        self.run_ground_truth_tests()
        self.save_reports()


if __name__ == "__main__":
    runner = ValidationRunner()
    runner.run_all()
