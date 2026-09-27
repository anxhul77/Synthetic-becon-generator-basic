import numpy as np
import pytest
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator

def test_ground_truth_coordinates():
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    gen = SyntheticBeaconGenerator(camera=cam)
    
    positions = [
        (960.0, 540.0),
        (1000.0, 540.0),
        (960.0, 600.0),
        (1200.0, 700.0),
        (500.0, 300.0),
    ]
    
    for x_req, y_req in positions:
        img, gt = gen.generate_frame(x0=x_req, y0=y_req, seed=42)
        
        # Verify exact requested coordinates
        assert gt["x_true"] == x_req
        assert gt["y_true"] == y_req
        
        # Independent analytical calculation of expected angles (DO NOT call cam.pixel_to_angle)
        expected_theta_x = float(np.arctan((x_req - 960.0) / 2000.0))
        expected_theta_y = float(np.arctan((y_req - 540.0) / 2000.0))
        
        assert pytest.approx(gt["theta_x_true"], abs=1e-12) == expected_theta_x
        assert pytest.approx(gt["theta_y_true"], abs=1e-12) == expected_theta_y

def test_ground_truth_metadata_completeness():
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    img, gt = gen.generate_frame(x0=960.0, y0=540.0, seed=42)
    
    required_keys = [
        "image_id", "seed", "generator_version", "width", "height",
        "x_true", "y_true", "theta_x_true", "theta_y_true",
        "amplitude", "attenuated_amplitude", "background", "background_type",
        "sigma_x", "sigma_y", "snr_db", "sigma_n", "psf_type", "noise_type",
        "range_km", "attenuation_alpha", "atmospheric_condition", "transmittance",
        "camera_fps", "fx", "fy", "cx", "cy"
    ]
    for key in required_keys:
        assert key in gt, f"Missing required ground truth key: {key}"
