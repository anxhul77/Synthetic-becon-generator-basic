import numpy as np
import pytest
from generator.background import UniformBackground, GradientBackground

def test_uniform_background():
    b0 = 15.5
    bg_model = UniformBackground(baseline=b0)
    img = bg_model.render(width=100, height=100)
    assert img.shape == (100, 100)
    assert np.all(img == b0)

def test_gradient_background_analytical():
    b0 = 10.0
    a = 0.02
    b = 0.01
    bg_model = GradientBackground(baseline=b0, a=a, b=b)
    img = bg_model.render(width=100, height=50)
    
    # Check corners and interior
    test_points = [(0, 0), (99, 0), (0, 49), (99, 49), (50, 25)]
    for x, y in test_points:
        expected = b0 + a * x + b * y
        assert pytest.approx(img[y, x], abs=1e-10) == expected

def test_gradient_background_non_negative():
    # Negative baseline and negative gradients that would physically be negative
    bg_model = GradientBackground(baseline=-5.0, a=-0.1, b=-0.1)
    img = bg_model.render(width=10, height=10)
    assert np.all(img >= 0.0)

def test_background_monotonicity():
    bg1 = UniformBackground(baseline=10.0).render(10, 10)
    bg2 = UniformBackground(baseline=20.0).render(10, 10)
    assert np.all(bg2 > bg1)
