import numpy as np
import pytest
from generator.psf import GaussianPSF, EllipticalGaussianPSF

def test_gaussian_psf_peak():
    psf = GaussianPSF(sigma_x=2.0, sigma_y=2.0)
    x = np.array([[960.0]])
    y = np.array([[540.0]])
    val = psf.render(x, y, x0=960.0, y0=540.0, amplitude=150.0)
    assert pytest.approx(val[0, 0], abs=1e-10) == 150.0

def test_gaussian_psf_one_sigma_response():
    sig_x, sig_y = 2.0, 3.0
    A = 100.0
    psf = GaussianPSF(sigma_x=sig_x, sigma_y=sig_y)
    
    # x0 + sig_x, y0
    xx = np.array([[960.0 + sig_x]])
    yy = np.array([[540.0]])
    val_x = psf.render(xx, yy, x0=960.0, y0=540.0, amplitude=A)
    assert pytest.approx(val_x[0, 0], abs=1e-10) == A * np.exp(-0.5)

    # x0, y0 + sig_y
    xx_y = np.array([[960.0]])
    yy_y = np.array([[540.0 + sig_y]])
    val_y = psf.render(xx_y, yy_y, x0=960.0, y0=540.0, amplitude=A)
    assert pytest.approx(val_y[0, 0], abs=1e-10) == A * np.exp(-0.5)

def test_gaussian_psf_2d_symmetry():
    psf = GaussianPSF(sigma_x=2.0, sigma_y=2.0)
    x_coords = np.arange(950, 971, dtype=np.float64)
    y_coords = np.arange(530, 551, dtype=np.float64)
    xx, yy = np.meshgrid(x_coords, y_coords)
    grid = psf.render(xx, yy, x0=960.0, y0=540.0, amplitude=100.0)
    
    # Check left-right symmetry and top-bottom symmetry
    np.testing.assert_allclose(grid, np.fliplr(grid), atol=1e-10)
    np.testing.assert_allclose(grid, np.flipud(grid), atol=1e-10)

def test_gaussian_psf_broadening_monotonicity():
    psf_narrow = GaussianPSF(sigma_x=1.0, sigma_y=1.0)
    psf_wide = GaussianPSF(sigma_x=3.0, sigma_y=3.0)
    
    # Point at offset 2 pixels from center
    xx = np.array([[962.0]])
    yy = np.array([[540.0]])
    val_narrow = psf_narrow.render(xx, yy, x0=960.0, y0=540.0, amplitude=100.0)[0, 0]
    val_wide = psf_wide.render(xx, yy, x0=960.0, y0=540.0, amplitude=100.0)[0, 0]
    
    assert val_wide > val_narrow

def test_gaussian_psf_peak_location():
    psf = GaussianPSF(sigma_x=2.0, sigma_y=2.0)
    x_coords = np.arange(950, 971, dtype=np.float64)
    y_coords = np.arange(530, 551, dtype=np.float64)
    xx, yy = np.meshgrid(x_coords, y_coords)
    grid = psf.render(xx, yy, x0=960.0, y0=540.0, amplitude=100.0)
    
    max_y_idx, max_x_idx = np.unravel_index(np.argmax(grid), grid.shape)
    assert x_coords[max_x_idx] == 960.0
    assert y_coords[max_y_idx] == 540.0

def test_elliptical_psf_anisotropy_and_rotation():
    A = 100.0
    sig_x, sig_y = 2.0, 5.0
    psf_0 = EllipticalGaussianPSF(sigma_x=sig_x, sigma_y=sig_y, theta_deg=0.0)
    psf_90 = EllipticalGaussianPSF(sigma_x=sig_x, sigma_y=sig_y, theta_deg=90.0)
    
    # Peak is at center
    xx_c = np.array([[960.0]])
    yy_c = np.array([[540.0]])
    assert pytest.approx(psf_0.render(xx_c, yy_c, 960.0, 540.0, A)[0, 0], abs=1e-10) == A
    assert pytest.approx(psf_90.render(xx_c, yy_c, 960.0, 540.0, A)[0, 0], abs=1e-10) == A
    
    # Check anisotropy at theta=0
    xx_offset = np.array([[962.0]])  # offset 2 along x
    yy_offset = np.array([[540.0 + 2.0]])  # offset 2 along y
    val_x0 = psf_0.render(xx_offset, yy_c, 960.0, 540.0, A)[0, 0]
    val_y0 = psf_0.render(xx_c, yy_offset, 960.0, 540.0, A)[0, 0]
    assert val_x0 != val_y0  # Anisotropic
    
    # Check theta=90 swaps axes (x offset at theta=90 equals y offset at theta=0)
    val_x90 = psf_90.render(xx_offset, yy_c, 960.0, 540.0, A)[0, 0]
    assert pytest.approx(val_x90, abs=1e-10) == val_y0
