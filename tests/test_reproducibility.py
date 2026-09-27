import numpy as np
import pytest
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator

def test_identical_seed_reproducibility():
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    
    seed = 12345
    img1, gt1 = gen.generate_frame(x0=960.0, y0=540.0, seed=seed)
    img2, gt2 = gen.generate_frame(x0=960.0, y0=540.0, seed=seed)
    
    np.testing.assert_array_equal(img1, img2)
    assert gt1["x_true"] == gt2["x_true"]
    assert gt1["y_true"] == gt2["y_true"]
    assert gt1["theta_x_true"] == gt2["theta_x_true"]
    assert gt1["theta_y_true"] == gt2["theta_y_true"]
    assert gt1["sigma_n"] == gt2["sigma_n"]

def test_different_seed_stochasticity():
    cam = PinholeCamera()
    gen = SyntheticBeaconGenerator(camera=cam)
    
    img1, gt1 = gen.generate_frame(x0=960.0, y0=540.0, snr_db=20.0, seed=12345)
    img2, gt2 = gen.generate_frame(x0=960.0, y0=540.0, snr_db=20.0, seed=67890)
    
    # Images differ due to noise realization
    assert not np.array_equal(img1, img2)
    
    # Deterministic ground-truth parameters remain identical
    assert gt1["x_true"] == gt2["x_true"]
    assert gt1["y_true"] == gt2["y_true"]
    assert gt1["theta_x_true"] == gt2["theta_x_true"]
    assert gt1["theta_y_true"] == gt2["theta_y_true"]
    assert gt1["attenuated_amplitude"] == gt2["attenuated_amplitude"]
