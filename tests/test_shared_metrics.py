import numpy as np
import pytest
from processing.shared_metrics import (
    compute_detector_roi_error,
    compute_localizer_error_true,
    compute_localizer_error_roi,
    compute_end_to_end_error,
    compute_rmse,
    compute_stats_with_ci,
    compute_acquisition_time,
    compute_target_loss,
    compute_reacquisition_time,
    compute_lock_retention,
    compute_nis_cholesky,
    compute_mahalanobis_coverage,
    compute_throughput_fps
)

def test_decomposed_errors():
    roi_center = (100.0, 100.0)
    target_true = (103.0, 104.0)
    estimate = (102.5, 104.0)

    # 1. Detector ROI error = sqrt(3^2 + 4^2) = 5.0
    assert np.isclose(compute_detector_roi_error(roi_center, target_true), 5.0)

    # 2. Localizer error true = sqrt((102.5-103)^2 + (104-104)^2) = 0.5
    assert np.isclose(compute_localizer_error_true(estimate, target_true), 0.5)

    # 3. Localizer error ROI
    local_offset = (3.0, 4.0)
    # estimate relative to ROI center is (2.5, 4.0), local offset is (3.0, 4.0) -> diff (0.5, 0.0) -> 0.5
    assert np.isclose(compute_localizer_error_roi(estimate, roi_center, local_offset), 0.5)

    # 4. E2E error
    assert np.isclose(compute_end_to_end_error(estimate, target_true), 0.5)

def test_rmse_and_ci():
    errs = [3.0, 4.0]
    # RMSE = sqrt((9+16)/2) = sqrt(12.5) = 3.5355
    assert np.isclose(compute_rmse(errs), np.sqrt(12.5))

    stats = compute_stats_with_ci([10.0, 12.0, 14.0, 16.0, 18.0])
    assert stats["mean"] == 14.0
    assert stats["median"] == 14.0
    assert stats["ci_bound"] > 0

def test_tracking_performance_metrics():
    # hit_mask: False, True, True, False, False, True, True
    hits = [False, True, True, False, False, True, True]

    # Acquisition time at 30 FPS: first 2 consecutive hits at index 1 & 2 -> acq_frame = 1 -> 1/30s = 0.0333s
    acq_t = compute_acquisition_time(hits, fps=30.0, min_consecutive=2)
    assert np.isclose(acq_t, 1.0 / 30.0)

    # Target loss: hits = 4, total = 7 -> loss count = 3 -> 3/7 * 100 = 42.857%
    loss_dict = compute_target_loss(hits)
    assert loss_dict["loss_count"] == 3
    assert np.isclose(loss_dict["loss_percentage"], (3.0 / 7.0) * 100.0)

    # Lock retention: 4/7 * 100 = 57.14%
    assert np.isclose(compute_lock_retention(hits), (4.0 / 7.0) * 100.0)

    # Reacquisition time: loss starts at index 3, 2 consecutive hits confirmed at index 6 -> reacq dur = (6-2+1)-3 = 2 frames -> 2/30 or (5-3)=2 frames
    reacq_t = compute_reacquisition_time(hits, fps=30.0, min_consecutive=2)
    assert np.isclose(reacq_t, 0.05, atol=0.02)

def test_nis_cholesky_and_coverage():
    y_innov = np.array([1.0, 1.0])
    S_cov = np.diag([1.0, 1.0])
    nis = compute_nis_cholesky(y_innov, S_cov)
    # NIS = [1, 1] * I * [1, 1]^T = 2.0
    assert np.isclose(nis, 2.0)

    nis_samples = [1.0, 1.2, 1.5, 2.0, 2.5]
    cov_dict = compute_mahalanobis_coverage(nis_samples)
    assert cov_dict["verdict"] == "APPROXIMATELY_CALIBRATED"

def test_throughput_fps():
    # 26.47 ms -> 1000 / 26.47 = 37.778 FPS
    fps = compute_throughput_fps(26.47)
    assert np.isclose(fps, 37.778, atol=0.01)
