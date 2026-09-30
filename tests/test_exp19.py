import pytest
import numpy as np
from experiments.exp19_fixed_vs_adaptive_eal.src.eal_search import (
    generate_fixed_eal,
    generate_adaptive_eal,
    check_acquisition
)

def test_fixed_eal_bounds_and_speed():
    cx, cy = 960.0, 540.0
    duration = 5.0
    fps = 30.0
    A_fixed = 100.0

    traj = generate_fixed_eal(cx, cy, A_fixed=A_fixed, duration_sec=duration, fps=fps)

    assert len(traj["u"]) == int(duration * fps)
    assert np.max(np.abs(traj["u"] - cx)) <= A_fixed + 1e-5
    assert np.max(np.abs(traj["v"] - cy)) <= A_fixed + 1e-5

def test_adaptive_eal_alignment():
    cx, cy = 960.0, 540.0
    Sigma_5 = np.array([[100.0, 0.0], [0.0, 25.0]])  # lambda1 = 100 (a=10), lambda2 = 25 (b=5)
    gamma = 2.4477  # sqrt(5.991)

    traj = generate_adaptive_eal(cx, cy, Sigma_5, gamma=gamma, duration_sec=5.0, fps=30.0)

    max_u_disp = np.max(np.abs(traj["u"] - cx))
    max_v_disp = np.max(np.abs(traj["v"] - cy))

    # Major axis along u should be gamma * 10
    np.testing.assert_allclose(max_u_disp, gamma * 10.0, rtol=0.1)
    np.testing.assert_allclose(max_v_disp, gamma * 5.0, rtol=0.1)

def test_acquisition_check():
    # Target stationary at (100, 100)
    search_u = np.linspace(0, 200, 100)
    search_v = np.full(100, 100.0)
    target_u = np.full(100, 100.0)
    target_v = np.full(100, 100.0)

    acq_idx, t_acq = check_acquisition(search_u, search_v, target_u, target_v, acq_radius=15.0, consec_frames=3, fps=30.0)

    assert acq_idx is not None
    assert t_acq > 0
