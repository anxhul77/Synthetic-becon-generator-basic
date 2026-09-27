import numpy as np
import pytest
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator

def test_full_frame_integration():
    cam = PinholeCamera(width=1920, height=1080)
    gen = SyntheticBeaconGenerator(camera=cam)
    
    img, gt = gen.generate_frame(x0=960.0, y0=540.0, bit_depth=8, seed=42)
    
    # Dimensions and datatype
    assert img.shape == (1080, 1920)
    assert img.dtype == np.uint8
    
    # Range and numerical validity
    assert np.all(img >= 0)
    assert np.all(img <= 255)
    assert not np.isnan(img).any()
    assert not np.isinf(img).any()
    
    # Ground truth completeness
    assert "x_true" in gt and gt["x_true"] == 960.0
    assert "y_true" in gt and gt["y_true"] == 540.0
    assert "theta_x_true" in gt and "theta_y_true" in gt
    assert "transmittance" in gt
    assert "sigma_n" in gt
    assert "fx" in gt and "fy" in gt and "cx" in gt and "cy" in gt

def test_noiseless_beacon_peak_location():
    cam = PinholeCamera(width=100, height=100, cx=50.0, cy=50.0)
    gen = SyntheticBeaconGenerator(camera=cam)
    
    x_req, y_req = 35.4, 62.8
    # Zero noise to test exact noiseless image centroid / peak
    img, gt = gen.generate_frame(
        x0=x_req, y0=y_req, amplitude=150.0, snr_db=100.0, background_level=10.0, bit_depth=64, seed=42
    )
    
    # Peak pixel location should be nearest integer pixel
    max_y, max_x = np.unravel_index(np.argmax(img), img.shape)
    assert max_x == int(round(x_req))
    assert max_y == int(round(y_req))

def test_quantization_8bit_and_float64():
    gen = SyntheticBeaconGenerator()
    
    img_8bit, _ = gen.generate_frame(bit_depth=8, seed=42)
    assert img_8bit.dtype == np.uint8
    assert np.min(img_8bit) >= 0
    assert np.max(img_8bit) <= 255
    
    img_float, _ = gen.generate_frame(bit_depth=64, seed=42)
    assert img_float.dtype == np.float64

def test_explicit_clipping_behavior():
    gen = SyntheticBeaconGenerator()
    
    # High amplitude + high background should clip at 255 for uint8
    img_high, _ = gen.generate_frame(
        amplitude=500.0, background_level=200.0, bit_depth=8, seed=42
    )
    assert np.max(img_high) == 255
    assert img_high.dtype == np.uint8
    
    # Negative noise excursion should clip to 0 (no negative values in uint8)
    img_neg_noise, _ = gen.generate_frame(
        amplitude=5.0, background_level=0.0, snr_db=0.0, bit_depth=8, seed=42
    )
    assert np.min(img_neg_noise) == 0
    assert img_neg_noise.dtype == np.uint8

def test_clipping_determinism():
    gen = SyntheticBeaconGenerator()
    img1, _ = gen.generate_frame(amplitude=500.0, bit_depth=8, seed=123)
    img2, _ = gen.generate_frame(amplitude=500.0, bit_depth=8, seed=123)
    np.testing.assert_array_equal(img1, img2)

def test_property_monotonicity_amplitude():
    gen = SyntheticBeaconGenerator()
    img_low, _ = gen.generate_frame(amplitude=50.0, snr_db=100.0, bit_depth=64, seed=42)
    img_high, _ = gen.generate_frame(amplitude=200.0, snr_db=100.0, bit_depth=64, seed=42)
    assert np.max(img_high) > np.max(img_low)

def test_property_monotonicity_background():
    gen = SyntheticBeaconGenerator()
    img_bg1, _ = gen.generate_frame(amplitude=0.0, background_level=10.0, snr_db=100.0, bit_depth=64, seed=42)
    img_bg2, _ = gen.generate_frame(amplitude=0.0, background_level=50.0, snr_db=100.0, bit_depth=64, seed=42)
    assert np.mean(img_bg2) > np.mean(img_bg1)

def test_property_beacon_movement():
    gen = SyntheticBeaconGenerator()
    img1, _ = gen.generate_frame(x0=500.0, y0=500.0, snr_db=100.0, bit_depth=64, seed=42)
    img2, _ = gen.generate_frame(x0=700.0, y0=500.0, snr_db=100.0, bit_depth=64, seed=42)
    
    max_y1, max_x1 = np.unravel_index(np.argmax(img1), img1.shape)
    max_y2, max_x2 = np.unravel_index(np.argmax(img2), img2.shape)
    
    assert max_x1 == 500
    assert max_x2 == 700
