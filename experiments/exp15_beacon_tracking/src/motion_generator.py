import numpy as np
from typing import Dict, Any, List, Tuple

class BeaconMotionGenerator:
    """
    Generates synthetic beacon trajectories (x(t), y(t)) and optical power profiles A(t)
    across continuous sequence frames t = 0..N-1 at a specified frame rate (FPS).
    """
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: float = 30.0,
        center_x: float = 960.0,
        center_y: float = 540.0
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.cx = center_x
        self.cy = center_y

    def generate_trajectory(
        self,
        motion_type: str,
        num_frames: int = 100,
        base_amplitude: float = 150.0,
        params: Dict[str, Any] = None,
        seed: int = 42
    ) -> Dict[str, np.ndarray]:
        """
        Generates 2D trajectory arrays:
        - x_true: [N] array of true x coordinates (pixels)
        - y_true: [N] array of true y coordinates (pixels)
        - vx_true: [N] array of true x velocities (px/s)
        - vy_true: [N] array of true y velocities (px/s)
        - amplitude: [N] array of beacon intensities
        - is_occluded: [N] boolean array indicating signal loss/occlusion
        """
        params = params or {}
        rng = np.random.default_rng(seed)
        t = np.arange(num_frames) / self.fps  # Time vector in seconds

        x_true = np.zeros(num_frames, dtype=np.float64)
        y_true = np.zeros(num_frames, dtype=np.float64)
        vx_true = np.zeros(num_frames, dtype=np.float64)
        vy_true = np.zeros(num_frames, dtype=np.float64)
        amplitude = np.full(num_frames, base_amplitude, dtype=np.float64)
        is_occluded = np.zeros(num_frames, dtype=bool)

        x0 = float(params.get("x0", self.cx))
        y0 = float(params.get("y0", self.cy))

        if motion_type in ["constant_velocity", "cv"]:
            vx = float(params.get("vx_px_per_sec", 30.0))
            vy = float(params.get("vy_px_per_sec", 15.0))
            x_true = x0 + vx * t
            y_true = y0 + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)

        elif motion_type in ["accelerating", "ca"]:
            vx0 = float(params.get("vx0", 10.0))
            vy0 = float(params.get("vy0", 5.0))
            ax = float(params.get("ax", 20.0))
            ay = float(params.get("ay", 10.0))
            x_true = x0 + vx0 * t + 0.5 * ax * (t ** 2)
            y_true = y0 + vy0 * t + 0.5 * ay * (t ** 2)
            vx_true = vx0 + ax * t
            vy_true = vy0 + ay * t

        elif motion_type in ["sinusoidal", "vibration"]:
            amp_x = float(params.get("amp_x", 100.0))
            amp_y = float(params.get("amp_y", 60.0))
            freq_x = float(params.get("freq_x", 0.5))  # Hz
            freq_y = float(params.get("freq_y", 0.8))  # Hz
            phi_x = float(params.get("phi_x", 0.0))
            phi_y = float(params.get("phi_y", np.pi / 4))

            omega_x = 2 * np.pi * freq_x
            omega_y = 2 * np.pi * freq_y

            x_true = x0 + amp_x * np.sin(omega_x * t + phi_x)
            y_true = y0 + amp_y * np.cos(omega_y * t + phi_y)
            vx_true = amp_x * omega_x * np.cos(omega_x * t + phi_x)
            vy_true = -amp_y * omega_y * np.sin(omega_y * t + phi_y)

        elif motion_type in ["random_maneuver", "random_walk"]:
            max_accel = float(params.get("max_accel", 50.0))
            dt = 1.0 / self.fps
            curr_x, curr_y = x0, y0
            curr_vx = float(params.get("vx0", 15.0))
            curr_vy = float(params.get("vy0", 10.0))
            curr_ax, curr_ay = 0.0, 0.0

            for k in range(num_frames):
                if k % int(max(1, self.fps * 0.5)) == 0:
                    curr_ax = rng.uniform(-max_accel, max_accel)
                    curr_ay = rng.uniform(-max_accel, max_accel)

                x_true[k] = curr_x
                y_true[k] = curr_y
                vx_true[k] = curr_vx
                vy_true[k] = curr_vy

                curr_vx += curr_ax * dt
                curr_vy += curr_ay * dt
                curr_x += curr_vx * dt
                curr_y += curr_vy * dt

        elif motion_type in ["occlusion_fade", "occlusion"]:
            vx = float(params.get("vx", 20.0))
            vy = float(params.get("vy", 10.0))
            x_true = x0 + vx * t
            y_true = y0 + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)

            fade_start = int(params.get("fade_start_frame", 35))
            fade_end = int(params.get("fade_end_frame", 55))

            for k in range(num_frames):
                if fade_start <= k < fade_end:
                    amplitude[k] = 0.0  # Total signal loss / cloud fade
                    is_occluded[k] = True

        else:
            raise ValueError(f"Unknown motion model type: {motion_type}")

        # Keep trajectory safely within sensor bounds
        margin = 35.0
        x_true = np.clip(x_true, margin, self.width - margin)
        y_true = np.clip(y_true, margin, self.height - margin)

        return {
            "time_sec": t,
            "x_true": x_true,
            "y_true": y_true,
            "vx_true": vx_true,
            "vy_true": vy_true,
            "amplitude": amplitude,
            "is_occluded": is_occluded,
            "motion_type": motion_type
        }
