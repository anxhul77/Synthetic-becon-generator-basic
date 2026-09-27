import numpy as np
import pytest
from generator.noise import GaussianNoise

def test_snr_to_sigma_equation():
    A = 150.0
    snr_levels = [40.0, 30.0, 20.0, 10.0, 5.0, 0.0]
    for snr in snr_levels:
        noise_model = GaussianNoise(snr_db=snr, amplitude=A)
        expected_sigma = A * (10.0 ** (-snr / 20.0))
        assert pytest.approx(noise_model.sigma_n, rel=1e-6) == expected_sigma

def test_noise_statistical_distribution():
    A = 150.0
    snr_db = 20.0
    noise_model = GaussianNoise(snr_db=snr_db, amplitude=A)
    expected_sigma = noise_model.sigma_n
    
    rng = np.random.default_rng(12345)
    dummy_img = np.zeros((1000, 1000), dtype=np.float64)
    noisy_img, sigma_returned = noise_model.add_noise(dummy_img, rng)
    
    noise_samples = noisy_img.ravel()
    sample_mean = float(np.mean(noise_samples))
    sample_std = float(np.std(noise_samples))
    
    assert pytest.approx(sigma_returned, rel=1e-6) == expected_sigma
    assert abs(sample_mean) < 0.05  # Mean near 0
    assert pytest.approx(sample_std, rel=0.02) == expected_sigma  # Within 2% of expected std

def test_noise_monotonicity():
    A = 150.0
    n_high_snr = GaussianNoise(snr_db=40.0, amplitude=A)
    n_low_snr = GaussianNoise(snr_db=10.0, amplitude=A)
    
    assert n_high_snr.sigma_n < n_low_snr.sigma_n
