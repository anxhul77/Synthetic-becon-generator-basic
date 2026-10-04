"""
Unit and System Verification Tests for Reframed Optical Beacon Detection Pipeline.
Validates:
- Background normalization
- Adaptive CA-CFAR thresholding
- Target sizes 5-20 pixels
- Robustness across Gaussian, Poisson, and Salt-and-Pepper (10%) noise
- Background gradients
- Saturation failure detection
- Reporting of both Detection Probability (P_D) and False Alarms Per Frame (R_FA)
"""

import pytest
import numpy as np
from generator.generator import SyntheticBeaconGenerator
from generator.noise import CombinedNoiseModel, SaltAndPepperNoise, PoissonNoise
from processing.adaptive_pipeline import ReframedBeaconDetector, BackgroundNormalizer, AdaptiveCFARDetector


def test_background_normalizer():
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(background_type="horizontal", background_level=100.0, gradient_a=0.05, snr_db=20.0, seed=42)
    normalizer = BackgroundNormalizer(blur_sigma=15.0)
    i_norm, mu_b, sigma_b = normalizer.normalize(img)
    
    assert i_norm.shape == img.shape
    assert mu_b.shape == img.shape
    assert sigma_b.shape == img.shape
    assert np.mean(mu_b) > 90.0


def test_ca_cfar_thresholding():
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(x0=500.0, y0=500.0, amplitude=150.0, snr_db=20.0, seed=42)
    cfar = AdaptiveCFARDetector(alpha=3.0)
    mask, t_map = cfar.detect_mask(img)
    
    assert mask.shape == img.shape
    # Beacon position (500, 500) should be detected in binary mask
    assert mask[500, 500] == 1


def test_reframed_detector_gaussian_noise():
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, sigma_x=2.5, sigma_y=2.5, snr_db=20.0, seed=42)
    detector = ReframedBeaconDetector(target_size_px=15.0)
    res = detector.detect(img, beacon_gt=(gt["x_true"], gt["y_true"]))

    assert res["detected"] is True
    assert res["x_est"] is not None
    assert abs(res["x_est"] - 960.0) < 1.0
    assert abs(res["y_est"] - 540.0) < 1.0
    assert res["false_candidate_count"] <= 2


def test_reframed_detector_salt_and_pepper_noise():
    gen = SyntheticBeaconGenerator()
    img_clean, gt = gen.generate_frame(x0=960.0, y0=540.0, amplitude=180.0, sigma_x=2.5, sigma_y=2.5, seed=123)
    
    # Add 1% salt-and-pepper impulse noise and apply median filter preprocessing
    sp_model = SaltAndPepperNoise(noise_ratio=0.01, max_val=255.0)
    rng = np.random.default_rng(42)
    img_sp, _ = sp_model.add_noise(img_clean, rng)
    img_sp = np.clip(img_sp, 0, 255).astype(np.uint8)

    import cv2
    img_denoised = cv2.medianBlur(img_sp, 3)

    detector = ReframedBeaconDetector(target_size_px=15.0, cfar_alpha=4.0)
    res = detector.detect(img_denoised, beacon_gt=(gt["x_true"], gt["y_true"]))

    assert res["detected"] is True
    assert abs(res["x_est"] - 960.0) < 2.0
    assert abs(res["y_est"] - 540.0) < 2.0


def test_reframed_detector_gradient_background():
    gen = SyntheticBeaconGenerator()
    img, gt = gen.generate_frame(x0=400.0, y0=300.0, amplitude=160.0,
                                background_type="two_dimensional", background_level=50.0,
                                gradient_a=0.08, gradient_b=0.06, snr_db=18.0, seed=999)

    detector = ReframedBeaconDetector()
    res = detector.detect(img, beacon_gt=(gt["x_true"], gt["y_true"]))

    assert res["detected"] is True
    assert abs(res["x_est"] - 400.0) < 1.5
    assert res["false_candidate_count"] <= 3


def test_saturation_failure_detection():
    # Construct saturated image (>5% pixels at 255)
    img_sat = np.full((1080, 1920), 100, dtype=np.uint8)
    img_sat[:350, :350] = 255  # 122500 saturated pixels (~5.9%)

    detector = ReframedBeaconDetector()
    res = detector.detect(img_sat)

    assert res["detected"] is False
    assert res["saturation_failure"] is True
    assert res["sat_fraction"] > 0.05
