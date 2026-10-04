"""
Unit tests for ROI Providers, Dual Evaluation Benchmark, and PSF Model Mismatch conditions.
"""

import os
import numpy as np
import pytest
import pandas as pd

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from generator.psf import get_psf_model, EllipticalGaussianPSF, AsymmetricPSF, DefocusedPSF, TurbulentPSF
from processing.roi_providers import (
    GroundTruthROIProvider,
    DetectorROIProvider,
    PreviousTrackStateROIProvider,
    PredictedStateROIProvider,
    ReacquisitionSearchROIProvider
)
from processing.benchmark_evaluator import DualBenchmarkEngine
from experiments.exp07_localization.src.psf_fitting import PSFFittingLocalization


def test_roi_providers_behavior():
    img = np.zeros((500, 500), dtype=np.float64)
    # Put a bright spot at (250, 250)
    xx, yy = np.meshgrid(np.arange(500), np.arange(500))
    img += 150.0 * np.exp(-0.5 * (((xx - 250.0) / 2.0)**2 + ((yy - 250.0) / 2.0)**2))

    x_true, y_true = 250.0, 250.0

    # 1. Ground Truth ROI Provider (Estimator-Only)
    gt_prov = GroundTruthROIProvider(roi_size=31)
    crop_gt = gt_prov.get_roi(img, x_true, y_true)
    assert crop_gt.roi_source_type == "estimator_only_gt"
    assert crop_gt.roi_image.shape == (31, 31)
    assert crop_gt.provider_label == "Estimator-Only (Ground-Truth ROI)"

    # 2. Detector ROI Provider (End-to-End)
    det_prov = DetectorROIProvider(roi_size=31, detector_type="classical", threshold=50.0)
    crop_det = det_prov.get_roi(img, x_true, y_true)
    assert crop_det.roi_source_type == "end_to_end_detector"
    assert crop_det.roi_image.shape == (31, 31)
    assert crop_det.detection_successful

    # 3. Previous Track State ROI Provider (End-to-End)
    prev_prov = PreviousTrackStateROIProvider(roi_size=31)
    crop_prev = prev_prov.get_roi(img, x_true, y_true, previous_track_state=(248.0, 251.0))
    assert crop_prev.roi_source_type == "end_to_end_previous_track"
    assert crop_prev.roi_image.shape == (31, 31)

    # 4. Predicted State ROI Provider (End-to-End)
    pred_prov = PredictedStateROIProvider(roi_size=31)
    crop_pred = pred_prov.get_roi(img, x_true, y_true, predicted_track_state=(252.0, 249.0))
    assert crop_pred.roi_source_type == "end_to_end_predicted_track"
    assert crop_pred.roi_image.shape == (31, 31)

    # 5. Reacquisition Search ROI Provider (End-to-End)
    reac_prov = ReacquisitionSearchROIProvider(roi_size=31)
    crop_reac = reac_prov.get_roi(img, x_true, y_true, predicted_track_state=(245.0, 245.0))
    assert crop_reac.roi_source_type == "end_to_end_reacquisition"
    assert crop_reac.roi_image.shape == (31, 31)


def test_psf_fitting_mismatch_conditions():
    xx, yy = np.meshgrid(np.arange(31, dtype=np.float64), np.arange(31, dtype=np.float64))

    # Condition 1: Unknown Width (true sigma=3.5 vs calibrated sigma=2.0)
    wide_img = 10.0 + 150.0 * np.exp(-0.5 * (((xx - 15.0) / 3.5)**2 + ((yy - 15.0) / 3.5)**2))
    calib_fitter = PSFFittingLocalization(calibrated_sigma_x=2.0, calibrated_sigma_y=2.0, estimate_width=False)
    est_w_fitter = PSFFittingLocalization(calibrated_sigma_x=2.0, calibrated_sigma_y=2.0, estimate_width=True)

    res_calib = calib_fitter._localize_roi(wide_img)
    res_est_w = est_w_fitter._localize_roi(wide_img)

    assert res_calib.success
    assert res_est_w.success
    assert pytest.approx(res_est_w.fit_parameters["calibrated_sigma_x"], abs=0.5) == 3.5

    # Condition 2: Elliptical PSF
    ell_psf = EllipticalGaussianPSF(sigma_x=1.5, sigma_y=3.5, theta_deg=0.0)
    ell_img = 10.0 + ell_psf.render(xx, yy, 15.0, 15.0, 150.0)
    res_ell = calib_fitter._localize_roi(ell_img)
    assert res_ell.success

    # Condition 3: Asymmetric PSF
    asym_psf = AsymmetricPSF(sigma=2.0, alpha=0.3, offset_x=1.5, offset_y=0.0)
    asym_img = 10.0 + asym_psf.render(xx, yy, 15.0, 15.0, 150.0)
    res_asym = calib_fitter._localize_roi(asym_img)
    assert res_asym.success

    # Condition 4: Defocused PSF
    def_psf = DefocusedPSF(sigma_nominal=2.0, sigma_defocus=2.0)
    def_img = 10.0 + def_psf.render(xx, yy, 15.0, 15.0, 150.0)
    res_def = calib_fitter._localize_roi(def_img)
    assert res_def.success

    # Condition 5: Turbulence PSF
    turb_psf = TurbulentPSF(sigma_nominal=2.0, r0_cm=4.0, speckle_strength=0.2)
    turb_img = 10.0 + turb_psf.render(xx, yy, 15.0, 15.0, 150.0)
    res_turb = calib_fitter._localize_roi(turb_img)
    assert res_turb.success


def test_dual_benchmark_engine_run():
    engine = DualBenchmarkEngine(output_dir="scratch/test_dual_benchmark_output", roi_size=31, seed=123)
    df_summary, df_raw, report = engine.run_benchmark(
        num_trials=2,
        snr_levels=[30.0, 15.0],
        psf_conditions=["nominal", "elliptical", "turbulence"],
        benchmark_mode="both"
    )

    assert len(df_raw) > 0
    assert len(df_summary) > 0
    assert "Estimator-Only Benchmark" in df_raw["eval_category"].values
    assert "End-to-End Benchmark" in df_raw["eval_category"].values
    assert os.path.exists("scratch/test_dual_benchmark_output/raw_benchmark_data.csv")
    assert os.path.exists("scratch/test_dual_benchmark_output/summary_benchmark.csv")
    assert os.path.exists("scratch/test_dual_benchmark_output/benchmark_report.md")
