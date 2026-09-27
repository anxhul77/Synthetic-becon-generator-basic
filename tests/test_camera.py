import numpy as np
import pytest
from generator.camera import PinholeCamera

def test_center_pixel_to_zero_angle():
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    tx, ty = cam.pixel_to_angle(960.0, 540.0)
    assert pytest.approx(tx, abs=1e-10) == 0.0
    assert pytest.approx(ty, abs=1e-10) == 0.0

def test_pixel_angle_roundtrip():
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    test_pixels = [
        (0.0, 0.0),
        (960.0, 540.0),
        (1919.0, 1079.0),
        (100.0, 700.0),
        (1500.0, 300.0),
    ]
    for u_orig, v_orig in test_pixels:
        tx, ty = cam.pixel_to_angle(u_orig, v_orig)
        u_rec, v_rec = cam.angle_to_pixel(tx, ty)
        assert pytest.approx(u_rec, abs=1e-10) == u_orig
        assert pytest.approx(v_rec, abs=1e-10) == v_orig

def test_fov_equations():
    w, h = 1920, 1080
    fx, fy = 2000.0, 2000.0
    cam = PinholeCamera(width=w, height=h, fx=fx, fy=fy, cx=960.0, cy=540.0)
    
    expected_fov_x = float(np.degrees(2.0 * np.arctan(w / (2.0 * fx))))
    expected_fov_y = float(np.degrees(2.0 * np.arctan(h / (2.0 * fy))))
    
    assert pytest.approx(cam.fov_x_deg, abs=1e-6) == expected_fov_x
    assert pytest.approx(cam.fov_y_deg, abs=1e-6) == expected_fov_y

def test_symmetry_around_principal_point():
    cam = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0, cx=960.0, cy=540.0)
    offsets = [10.0, 50.0, 200.0, 500.0]
    for d in offsets:
        tx_left, _ = cam.pixel_to_angle(cam.cx - d, cam.cy)
        tx_right, _ = cam.pixel_to_angle(cam.cx + d, cam.cy)
        assert pytest.approx(tx_left, abs=1e-10) == -tx_right
        assert pytest.approx(abs(tx_left), abs=1e-10) == abs(tx_right)

        _, ty_top = cam.pixel_to_angle(cam.cx, cam.cy - d)
        _, ty_bottom = cam.pixel_to_angle(cam.cx, cam.cy + d)
        assert pytest.approx(ty_top, abs=1e-10) == -ty_bottom

def test_focal_length_fov_monotonicity():
    cam1 = PinholeCamera(width=1920, height=1080, fx=1000.0, fy=1000.0)
    cam2 = PinholeCamera(width=1920, height=1080, fx=2000.0, fy=2000.0)
    assert cam1.fov_x_deg > cam2.fov_x_deg
    assert cam1.fov_y_deg > cam2.fov_y_deg
