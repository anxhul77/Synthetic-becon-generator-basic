import os
import numpy as np
import pytest
import pandas as pd

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from experiments.exp07_localization.src.roi_extractor import ROIExtractor, roi_to_full_coords, full_to_roi_coords
from experiments.exp07_localization.src.bounding_box_center import BoundingBoxCenterLocalization
from experiments.exp07_localization.src.binary_centroid import BinaryCentroidLocalization
from experiments.exp07_localization.src.intensity_weighted_centroid import IntensityWeightedCentroidLocalization
from experiments.exp07_localization.src.gaussian_fitting import GaussianFittingLocalization
from experiments.exp07_localization.src.psf_fitting import PSFFittingLocalization
from experiments.exp07_localization.src.localization_evaluation import (
    compute_pixel_and_angular_errors,
    compute_group_summary_stats,
    compute_paired_comparison
)
from experiments.exp07_localization.src.run_experiment import Exp07Localization


# =====================================================================
# 1. ROI Extractor Tests
# =====================================================================
def test_roi_extractor_dimensions_and_origin():
    img = np.zeros((1080, 1920), dtype=np.float64)
    x_true, y_true = 960.25, 540.75
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(img, x_true, y_true)

    assert crop.roi_image.shape == (31, 31)
    assert crop.width == 31 and crop.height == 31
    assert crop.xmin == 960 - 15  # 945
    assert crop.ymin == 541 - 15  # 526
    assert pytest.approx(crop.x_true_roi, abs=1e-5) == x_true - crop.xmin
    assert pytest.approx(crop.y_true_roi, abs=1e-5) == y_true - crop.ymin
    assert not crop.is_out_of_bounds


def test_roi_coordinate_conversion():
    xmin, ymin = 100, 200
    x_roi, y_roi = 15.5, 15.5
    xf, yf = roi_to_full_coords(x_roi, y_roi, xmin, ymin)
    assert xf == 115.5 and yf == 215.5

    xr, yr = full_to_roi_coords(xf, yf, xmin, ymin)
    assert xr == 15.5 and yr == 15.5


def test_roi_extractor_boundary_handling():
    img = np.zeros((100, 100), dtype=np.float64)
    extractor = ROIExtractor(roi_size=31)
    # Crop near top-left edge
    crop = extractor.extract_roi(img, 5.0, 5.0)
    assert crop.roi_image.shape == (31, 31)
    assert crop.is_out_of_bounds


# =====================================================================
# 2. Bounding-Box Center Tests
# =====================================================================
def test_bounding_box_center_known_shape():
    roi = np.full((31, 31), 10.0, dtype=np.float64)
    # 5x5 bright box centered at (15, 15) -> x: 13..17, y: 13..17
    roi[13:18, 13:18] = 200.0

    algo = BoundingBoxCenterLocalization(threshold_offset=15.0)
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = roi

    res = algo.localize(crop)
    assert res.success
    assert pytest.approx(res.x_roi, abs=1e-5) == 15.0
    assert pytest.approx(res.y_roi, abs=1e-5) == 15.0


def test_bounding_box_center_empty_mask_failure():
    roi = np.full((31, 31), 10.0, dtype=np.float64)
    algo = BoundingBoxCenterLocalization(threshold_offset=50.0)
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = roi

    res = algo.localize(crop)
    assert not res.success
    assert "No foreground pixels" in res.failure_reason


# =====================================================================
# 3. Binary Centroid Tests
# =====================================================================
def test_binary_centroid_symmetric_and_asymmetric():
    roi = np.full((31, 31), 10.0, dtype=np.float64)
    # Asymmetric shape: (10, 10), (10, 11), (11, 10) -> mean x = 10.333, mean y = 10.333
    roi[10, 10] = 200.0
    roi[10, 11] = 200.0
    roi[11, 10] = 200.0

    algo = BinaryCentroidLocalization(threshold_offset=15.0)
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = roi

    res = algo.localize(crop)
    assert res.success
    assert pytest.approx(res.x_roi, abs=1e-2) == 10.333333
    assert pytest.approx(res.y_roi, abs=1e-2) == 10.333333


# =====================================================================
# 4. Intensity-Weighted Centroid Tests
# =====================================================================
def test_intensity_weighted_centroid():
    roi = np.full((31, 31), 10.0, dtype=np.float64)
    # Peak at (15, 15) with intensity 110 (weight 100), neighbor at (16, 15) intensity 60 (weight 50)
    roi[15, 15] = 110.0
    roi[15, 16] = 60.0

    algo = IntensityWeightedCentroidLocalization(bg_model_type="border")
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = roi

    res = algo.localize(crop)
    assert res.success
    # Expected weighted x = (15*100 + 16*50) / 150 = 15.3333
    assert pytest.approx(res.x_roi, abs=1e-3) == 15.333333
    assert pytest.approx(res.y_roi, abs=1e-3) == 15.0


def test_intensity_weighted_centroid_zero_weight_failure():
    roi = np.full((31, 31), 10.0, dtype=np.float64)
    algo = IntensityWeightedCentroidLocalization()
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = roi

    res = algo.localize(crop)
    assert not res.success
    assert "weight is zero" in res.failure_reason


# =====================================================================
# 5. Gaussian Fitting Tests
# =====================================================================
def test_gaussian_fitting_noiseless_recovery():
    # Synthetic 2D Gaussian at (15.4, 15.6) with amp=150, sigma=2.0, bg=10
    xx, yy = np.meshgrid(np.arange(31, dtype=np.float64), np.arange(31, dtype=np.float64))
    gauss = 10.0 + 150.0 * np.exp(-0.5 * (((xx - 15.4) / 2.0)**2 + ((yy - 15.6) / 2.0)**2))

    algo = GaussianFittingLocalization()
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = gauss

    res = algo.localize(crop)
    assert res.success
    assert pytest.approx(res.x_roi, abs=1e-2) == 15.4
    assert pytest.approx(res.y_roi, abs=1e-2) == 15.6


# =====================================================================
# 6. PSF Fitting Tests
# =====================================================================
def test_psf_fitting_noiseless_recovery():
    xx, yy = np.meshgrid(np.arange(31, dtype=np.float64), np.arange(31, dtype=np.float64))
    psf_img = 10.0 + 150.0 * np.exp(-0.5 * (((xx - 15.2) / 2.0)**2 + ((yy - 15.8) / 2.0)**2))

    algo = PSFFittingLocalization(calibrated_sigma_x=2.0, calibrated_sigma_y=2.0)
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(np.zeros((1000, 1000)), 500.0, 500.0)
    crop.roi_image = psf_img

    res = algo.localize(crop)
    assert res.success
    assert pytest.approx(res.x_roi, abs=1e-2) == 15.2
    assert pytest.approx(res.y_roi, abs=1e-2) == 15.8


# =====================================================================
# 7. Evaluation & Angular Conversion Tests
# =====================================================================
def test_evaluation_metrics_and_angular_conversion():
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    res = compute_pixel_and_angular_errors(962.0, 540.0, 960.0, 540.0, cam)

    assert res["error_x"] == 2.0
    assert res["error_y"] == 0.0
    assert res["radial_error"] == 2.0
    assert res["angular_error_urad"] > 0.0

    # Failed localization error test
    failed_res = compute_pixel_and_angular_errors(None, None, 960.0, 540.0, cam)
    assert failed_res["error_x"] is None
    assert failed_res["radial_error"] is None


# =====================================================================
# 8. Integration & Reproducibility Test
# =====================================================================
def test_exp07_integration_and_reproducibility():
    exp = Exp07Localization(results_dir="scratch/test_exp07_results")
    df_summary, df_paired, df_raw, report = exp.run(trials_override=2)

    assert len(df_raw) > 0
    assert len(df_summary) > 0
    assert len(df_paired) > 0
    assert os.path.exists(os.path.join(exp.results_dir, exp.experiment_id, "raw_data.csv"))
    assert os.path.exists(os.path.join(exp.results_dir, exp.experiment_id, "summary.csv"))
    assert os.path.exists(os.path.join(exp.results_dir, exp.experiment_id, "paired_comparison.csv"))
    assert os.path.exists(os.path.join(exp.results_dir, exp.experiment_id, "report.md"))

    # Test all 5 algorithms present in raw data
    methods = set(df_raw["method_name"].unique())
    expected_methods = {
        "Bounding Box Center",
        "Binary Centroid",
        "Intensity-Weighted Centroid",
        "Gaussian Fitting",
        "PSF Fitting (Known PSF)"
    }
    assert expected_methods.issubset(methods)
