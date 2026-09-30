import pytest
import numpy as np
import pandas as pd
import os
import tempfile
import yaml

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from generator.psf import GaussianPSF

from experiments.exp07_localization.src.roi_extractor import ROIExtractor
from experiments.exp07_localization.src.intensity_weighted_centroid import IntensityWeightedCentroidLocalization
from experiments.exp07_localization.src.gaussian_fitting import GaussianFittingLocalization
from experiments.exp07_localization.src.psf_fitting import PSFFittingLocalization
from experiments.exp07_localization.src.localization_evaluation import (
    compute_pixel_and_angular_errors,
    compute_group_summary_stats,
    compute_paired_comparison
)

from experiments.exp09_psf_width import Exp09PSFWidth
from experiments.exp09_psf_width.src.energy_scaler import (
    calculate_fixed_energy_amplitude,
    measure_rendered_signal_energy
)


def test_psf_sigma_acceptance_and_rejection():
    """Verify that all 7 valid PSF widths are accepted and nonpositive values raise errors."""
    valid_sigmas = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    for s in valid_sigmas:
        psf = GaussianPSF(sigma_x=s, sigma_y=s)
        assert psf.sigma_x == s
        assert psf.sigma_y == s

    with pytest.raises(ValueError):
        calculate_fixed_energy_amplitude(0.0)

    with pytest.raises(ValueError):
        calculate_fixed_energy_amplitude(-1.0)


def test_fractional_beacon_coordinates_preservation():
    """Verify ground-truth fractional coordinates and phases are preserved."""
    camera = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=camera)
    x0, y0 = 960.375, 540.625
    img, gt = gen.generate_frame(x0=x0, y0=y0, sigma_x=2.0, sigma_y=2.0, seed=42)

    assert gt["x_true"] == pytest.approx(x0)
    assert gt["y_true"] == pytest.approx(y0)
    assert gt["phi_x"] == pytest.approx(0.375)
    assert gt["phi_y"] == pytest.approx(0.625)


def test_psf_sigma_profile_change():
    """Verify changing PSF sigma changes rendered PSF profile intensity distribution."""
    camera = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=camera)
    img_narrow, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=0.5, sigma_y=0.5, seed=42, snr_db=60.0)
    img_wide, _ = gen.generate_frame(x0=960.0, y0=540.0, sigma_x=4.0, sigma_y=4.0, seed=42, snr_db=60.0)

    # Off-center pixel intensity (2 pixels away from center) should be significantly higher for wide PSF
    assert float(img_wide[540, 962]) > float(img_narrow[540, 962])
    assert not np.array_equal(img_narrow, img_wide)



def test_reproducibility_identical_seeds():
    """Verify identical seeds produce identical synthetic images."""
    camera = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=camera)
    img1, _ = gen.generate_frame(x0=960.25, y0=540.75, sigma_x=1.5, sigma_y=1.5, seed=1234)
    img2, _ = gen.generate_frame(x0=960.25, y0=540.75, sigma_x=1.5, sigma_y=1.5, seed=1234)

    assert np.array_equal(img1, img2)


def test_identical_image_and_roi_across_estimators():
    """Verify all three estimators receive identical images and ROIs."""
    camera = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=camera)
    img, gt = gen.generate_frame(x0=960.25, y0=540.75, sigma_x=2.0, sigma_y=2.0, seed=99)
    extractor = ROIExtractor(roi_size=31)
    crop = extractor.extract_roi(img, gt["x_true"], gt["y_true"])

    alg_wc = IntensityWeightedCentroidLocalization()
    alg_gf = GaussianFittingLocalization()
    alg_pf = PSFFittingLocalization(calibrated_sigma_x=2.0, calibrated_sigma_y=2.0)

    res_wc = alg_wc.localize(crop)
    res_gf = alg_gf.localize(crop)
    res_pf = alg_pf.localize(crop)

    assert res_wc.success
    assert res_gf.success
    assert res_pf.success


def test_noiseless_finite_localization():
    """Verify estimators produce finite, accurate results on high SNR images."""
    camera = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=camera)
    img, gt = gen.generate_frame(x0=960.3, y0=540.4, sigma_x=2.0, sigma_y=2.0, snr_db=60.0, seed=77)
    crop = ROIExtractor(roi_size=31).extract_roi(img, gt["x_true"], gt["y_true"])

    alg_wc = IntensityWeightedCentroidLocalization()
    alg_gf = GaussianFittingLocalization()
    alg_pf = PSFFittingLocalization(calibrated_sigma_x=2.0, calibrated_sigma_y=2.0)

    for alg in [alg_wc, alg_gf, alg_pf]:
        res = alg.localize(crop)
        assert res.success
        assert np.isfinite(res.x_est)
        assert np.isfinite(res.y_est)
        err = np.sqrt((res.x_est - 960.3)**2 + (res.y_est - 540.4)**2)
        assert err < 0.2


def test_angular_error_calculation():
    """Verify angular error uses pinhole camera model equations."""
    camera = PinholeCamera(fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    x_true, y_true = 960.0, 540.0
    x_est, y_est = 962.0, 540.0  # 2 pixels offset along X

    err_dict = compute_pixel_and_angular_errors(x_est, y_est, x_true, y_true, camera)
    assert err_dict["error_x"] == pytest.approx(2.0)
    assert err_dict["error_y"] == pytest.approx(0.0)
    assert err_dict["radial_error"] == pytest.approx(2.0)
    assert err_dict["angular_error_urad"] == pytest.approx(1000.0, rel=1e-3)


def test_failed_localization_exclusion():
    """Verify failed localizations are excluded from RMSE stats but included in total trials."""
    df = pd.DataFrame([
        {"success": True, "error_x": 0.1, "error_y": 0.2, "radial_error": 0.2236, "angular_error_urad": 111.8, "runtime_ms": 1.0},
        {"success": False, "error_x": None, "error_y": None, "radial_error": None, "angular_error_urad": None, "runtime_ms": 2.0}
    ])
    stats = compute_group_summary_stats(df, num_bootstraps=100)
    assert stats["total_trials"] == 2
    assert stats["success_count"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["radial_rmse"] == pytest.approx(0.2236, abs=1e-3)



def test_fixed_energy_amplitude_scaling():
    """Verify fixed-energy amplitude scaling formula A(sigma) = A_ref * (sigma_ref^2 / sigma^2)."""
    amp_ref = 150.0
    sig_ref = 2.0
    a_05 = calculate_fixed_energy_amplitude(0.5, amplitude_ref=amp_ref, sigma_ref=sig_ref)
    a_40 = calculate_fixed_energy_amplitude(4.0, amplitude_ref=amp_ref, sigma_ref=sig_ref)

    assert a_05 == pytest.approx(150.0 * (4.0 / 0.25))  # 2400
    assert a_40 == pytest.approx(150.0 * (4.0 / 16.0))  # 37.5


def test_exp09_smoke_run():
    """Runs a quick end-to-end smoke test for Exp09PSFWidth execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        exp = Exp09PSFWidth(results_dir=tmpdir)
        df_summary, df_phase, df_paired, df_raw, report = exp.run(trials_override=2)

        assert not df_raw.empty
        assert not df_summary.empty
        assert not df_paired.empty
        assert os.path.exists(os.path.join(tmpdir, "exp09_psf_width", "raw_data.csv"))
        assert os.path.exists(os.path.join(tmpdir, "exp09_psf_width", "summary.csv"))
        assert os.path.exists(os.path.join(tmpdir, "exp09_psf_width", "report.md"))
