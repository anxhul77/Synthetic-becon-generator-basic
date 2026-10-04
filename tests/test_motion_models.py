import hashlib
import numpy as np
import pytest

from experiments.exp15_beacon_tracking.src.motion_generator import BeaconMotionGenerator


def test_motion_models_uniqueness_and_properties():
    motion_gen = BeaconMotionGenerator(width=640, height=480, fps=30.0, center_x=320.0, center_y=240.0)
    
    models = [
        "straight_line",
        "circular",
        "figure_eight",
        "random_walk",
        "sinusoidal",
        "accelerating",
        "camera_jitter",
        "platform_motion",
        "fov_boundary_entry",
        "fov_exit_reentry",
        "atmospheric_degradation"
    ]

    hashes = {}
    trajectories = {}

    for model in models:
        traj = motion_gen.generate_trajectory(motion_type=model, num_frames=150, seed=12345)
        x_true = traj["x_true"]
        y_true = traj["y_true"]

        # Calculate MD5 hash from raw x_true and y_true bytes
        raw_bytes = x_true.tobytes() + y_true.tobytes()
        t_hash = hashlib.md5(raw_bytes).hexdigest()[:10]

        hashes[model] = t_hash
        trajectories[model] = traj

    # Assertion 1: All 11 motion models must have distinct trajectory hashes!
    unique_hashes = set(hashes.values())
    assert len(unique_hashes) == len(models), (
        f"Duplicate trajectory hashes detected! Hashes: {hashes}"
    )

    # Assertion 2: Circular trajectory radius from center (320, 240) must equal specified radius
    circ_traj = trajectories["circular"]
    r_calc = np.hypot(circ_traj["x_true"] - 320.0, circ_traj["y_true"] - 240.0)
    assert np.allclose(r_calc, 80.0, atol=2.0), "Circular trajectory does not maintain expected orbit radius!"
    assert np.std(circ_traj["x_true"]) > 10.0 and np.std(circ_traj["y_true"]) > 10.0, "Circular trajectory must oscillate on both axes!"

    # Assertion 3: Figure eight trajectory oscillates on both axes with frequency ratio 1:2
    fig8_traj = trajectories["figure_eight"]
    assert np.std(fig8_traj["x_true"]) > 15.0 and np.std(fig8_traj["y_true"]) > 10.0, "Figure-8 trajectory must move on both axes!"
    # Zero crossings in x vs y
    x_cross = np.sum(np.diff(np.sign(fig8_traj["x_true"] - 320.0)) != 0)
    y_cross = np.sum(np.diff(np.sign(fig8_traj["y_true"] - 240.0)) != 0)
    assert y_cross >= x_cross, "Figure-eight y-axis must oscillate faster than x-axis!"

    # Assertion 4: Sinusoidal trajectory has measurable periodicity
    sin_traj = trajectories["sinusoidal"]
    assert np.std(sin_traj["x_true"]) > 20.0, "Sinusoidal trajectory must show non-zero amplitude!"

    # Assertion 5: Accelerating trajectory has changing velocity
    acc_traj = trajectories["accelerating"]
    v_start = np.hypot(acc_traj["vx_true"][0], acc_traj["vy_true"][0])
    v_end = np.hypot(acc_traj["vx_true"][-1], acc_traj["vy_true"][-1])
    assert v_end > v_start + 10.0, "Accelerating trajectory must have increasing velocity!"

    # Assertion 6: Random walk is not identical to constant velocity
    rw_traj = trajectories["random_walk"]
    cv_traj = trajectories["straight_line"]
    assert not np.array_equal(rw_traj["x_true"], cv_traj["x_true"]), "Random walk must not match constant velocity!"
