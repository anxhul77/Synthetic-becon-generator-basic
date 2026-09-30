import pytest
import numpy as np
import pandas as pd
import os
import tempfile

from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from generator.psf import (
    GaussianPSF,
    EllipticalGaussianPSF,
    AsymmetricPSF,
    DefocusedPSF,
    AberratedPSF,
    get_psf_model
)

from experiments.exp07_localization.src.roi_extractor import ROIExtractor
from experiments.exp07_localization.src.intensity_weighted_centroid import IntensityWeightedCentroidLocalization
from experiments.exp07_localization.src.gaussian_fitting import GaussianFittingLocalization
from experiments.exp10_psf_mismatch.src.psf_aware_fitting import PSFAwareFittingLocalization
from experiments.exp10_psf_mismatch import Exp10PSFMismatch


def test_gaussian_psf_matches_established():
    """Verify GaussianPSF matches established rendering."""
    psf = GaussianPSF(sigma_x=2.0, sigma_y=2.0)
    xx, yy = np.meshgrid(np.arange(31), np.arange(31))
    signal = psf.render(xx, yy, x0=15.0, y0=15.0, amplitude=150.0)
    assert signal[15, 15] == pytest.approx(150.0)


def test_elliptical_psf_axis_ratio_and_orientation():
    """Verify EllipticalGaussianPSF applies axis ratio and rotation angle."""
    psf_0 = EllipticalGaussianPSF(sigma_x=2.0, sigma_y=4.0, theta_deg=0.0)
    psf_45 = EllipticalGaussianPSF(sigma_x=2.0, sigma_y=4.0, theta_deg=45.0)

    xx, yy = np.meshgrid(np.arange(31), np.arange(31))
    sig_0 = psf_0.render(xx, yy, 15.0, 15.0, 150.0)
    sig_45 = psf_45.render(xx, yy, 15.0, 15.0, 150.0)

    assert sig_0[15, 17] != sig_0[17, 15]  # Anisotropic
    assert not np.array_equal(sig_0, sig_45)


def test_asymmetric_psf_profile():
    """Verify AsymmetricPSF introduces secondary displaced peak profile."""
    psf = AsymmetricPSF(sigma=2.0, alpha=0.3, offset_x=2.0, offset_y=0.0)
    xx, yy = np.meshgrid(np.arange(31), np.arange(31))
    sig = psf.render(xx, yy, 15.0, 15.0, 150.0)

    # Off-center secondary component along +X should have higher signal than -X
    assert float(sig[15, 17]) > float(sig[15, 13])


def test_defocused_psf_expansion():
    """Verify DefocusedPSF expands effective spot sigma."""
    psf_foc = DefocusedPSF(sigma_nominal=2.0, sigma_defocus=0.0)
    psf_def = DefocusedPSF(sigma_nominal=2.0, sigma_defocus=2.0)

    assert psf_foc.sigma_eff == pytest.approx(2.0)
    assert psf_def.sigma_eff == pytest.approx(np.sqrt(8.0))

    xx, yy = np.meshgrid(np.arange(31), np.arange(31))
    s_foc = psf_foc.render(xx, yy, 15.0, 15.0, 150.0)
    s_def = psf_def.render(xx, yy, 15.0, 15.0, 150.0)

    # Defocused PSF has broader spatial footprint
    assert float(s_def[15, 19]) > float(s_foc[15, 19])


def test_aberrated_psf_distortion():
    """Verify AberratedPSF alters Gaussian core with optical distortion."""
    psf = AberratedPSF(sigma=2.0, aberration_type="coma", strength_waves=0.2)
    xx, yy = np.meshgrid(np.arange(31), np.arange(31))
    sig = psf.render(xx, yy, 15.0, 15.0, 150.0)

    assert sig[15, 15] == pytest.approx(150.0)
    assert not np.array_equal(sig, np.rot90(sig))


def test_factory_function_instantiation():
    """Verify get_psf_model returns valid PSFModel instances."""
    p_g = get_psf_model("gaussian", sigma=2.0)
    p_e = get_psf_model("elliptical", sigma_x=2.0, sigma_y=3.0)
    p_a = get_psf_model("asymmetric", alpha=0.2)
    p_d = get_psf_model("defocused", blur_sigma_px=1.0)
    p_ab = get_psf_model("aberrated", strength_waves=0.1)

    assert isinstance(p_g, GaussianPSF)
    assert isinstance(p_e, EllipticalGaussianPSF)
    assert isinstance(p_a, AsymmetricPSF)
    assert isinstance(p_d, DefocusedPSF)
    assert isinstance(p_ab, AberratedPSF)


def test_identical_images_across_estimators():
    """Verify all estimators receive identical images and ROIs."""
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(x0=960.2, y0=540.3, psf_type="elliptical", sigma_x=2.0, sigma_y=3.0, seed=55)
    crop = ROIExtractor(roi_size=31).extract_roi(img, gt["x_true"], gt["y_true"])

    alg_wc = IntensityWeightedCentroidLocalization()
    alg_gf = GaussianFittingLocalization()
    alg_pf = PSFAwareFittingLocalization(psf_family="elliptical", sigma_x=2.0, sigma_y=3.0)

    res_wc = alg_wc.localize(crop)
    res_gf = alg_gf.localize(crop)
    res_pf = alg_pf.localize(crop)

    assert res_wc.success
    assert res_gf.success
    assert res_pf.success


def test_exp10_smoke_run():
    """Runs end-to-end smoke test for Exp10PSFMismatch execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        exp = Exp10PSFMismatch(results_dir=tmpdir)
        df_summary, df_phase, df_paired, df_mismatch, df_raw, report = exp.run(trials_override=2)

        assert not df_raw.empty
        assert not df_summary.empty
        assert not df_mismatch.empty
        assert os.path.exists(os.path.join(tmpdir, "exp10_psf_mismatch", "raw_data.csv"))
        assert os.path.exists(os.path.join(tmpdir, "exp10_psf_mismatch", "summary.csv"))
        assert os.path.exists(os.path.join(tmpdir, "exp10_psf_mismatch", "mismatch_penalty.csv"))
        assert os.path.exists(os.path.join(tmpdir, "exp10_psf_mismatch", "report.md"))
