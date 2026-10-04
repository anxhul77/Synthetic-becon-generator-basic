import numpy as np
from typing import Dict, Any, List, Tuple

class BeaconMotionGenerator:
    """
    Generates synthetic beacon trajectories (x(t), y(t)) and optical power profiles A(t)
    across continuous sequence frames t = 0..N-1 at a specified frame rate (FPS).
    Supports 11 distinct motion models with unique mathematical signatures.
    """
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: float = 30.0,
        center_x: float = 320.0,
        center_y: float = 240.0
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.cx = center_x
        self.cy = center_y

    def generate_trajectory(
        self,
        motion_type: str,
        num_frames: int = 150,
        base_amplitude: float = 150.0,
        params: Dict[str, Any] = None,
        seed: int = 42
    ) -> Dict[str, np.ndarray]:
        params = params or {}
        rng = np.random.default_rng(seed)
        t = np.arange(num_frames, dtype=np.float64) / self.fps  # Time vector in seconds

        x_true = np.zeros(num_frames, dtype=np.float64)
        y_true = np.zeros(num_frames, dtype=np.float64)
        vx_true = np.zeros(num_frames, dtype=np.float64)
        vy_true = np.zeros(num_frames, dtype=np.float64)
        amplitude = np.full(num_frames, base_amplitude, dtype=np.float64)
        is_occluded = np.zeros(num_frames, dtype=bool)

        x0 = float(params.get("x0", self.cx))
        y0 = float(params.get("y0", self.cy))

        if motion_type in ["straight_line", "constant_velocity", "cv"]:
            vx = float(params.get("vx_px_per_sec", 35.0))
            vy = float(params.get("vy_px_per_sec", 20.0))
            x_true = x0 + vx * t
            y_true = y0 + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)

        elif motion_type in ["circular", "orbit"]:
            radius = float(params.get("radius", 80.0))
            omega = float(params.get("omega", 1.5))  # rad/s
            phi = float(params.get("phi", 0.0))
            x_true = x0 + radius * np.cos(omega * t + phi)
            y_true = y0 + radius * np.sin(omega * t + phi)
            vx_true = -radius * omega * np.sin(omega * t + phi)
            vy_true = radius * omega * np.cos(omega * t + phi)

        elif motion_type in ["figure_eight", "lissajous"]:
            radius_x = float(params.get("radius_x", 100.0))
            radius_y = float(params.get("radius_y", 60.0))
            omega = float(params.get("omega", 1.2))  # rad/s
            x_true = x0 + radius_x * np.sin(omega * t)
            y_true = y0 + radius_y * np.sin(2.0 * omega * t)
            vx_true = radius_x * omega * np.cos(omega * t)
            vy_true = 2.0 * radius_y * omega * np.cos(2.0 * omega * t)

        elif motion_type in ["random_walk", "random_maneuver"]:
            max_accel = float(params.get("max_accel", 60.0))
            dt = 1.0 / self.fps
            curr_x, curr_y = x0, y0
            curr_vx = float(params.get("vx0", 15.0))
            curr_vy = float(params.get("vy0", 10.0))
            curr_ax, curr_ay = 0.0, 0.0

            for k in range(num_frames):
                if k % int(max(1, self.fps * 0.4)) == 0:
                    curr_ax = float(rng.uniform(-max_accel, max_accel))
                    curr_ay = float(rng.uniform(-max_accel, max_accel))

                x_true[k] = curr_x
                y_true[k] = curr_y
                vx_true[k] = curr_vx
                vy_true[k] = curr_vy

                curr_vx += curr_ax * dt
                curr_vy += curr_ay * dt
                curr_x += curr_vx * dt
                curr_y += curr_ay * dt

        elif motion_type in ["sinusoidal", "wave"]:
            amp_x = float(params.get("amp_x", 120.0))
            amp_y = float(params.get("amp_y", 70.0))
            freq_x = float(params.get("freq_x", 0.6))
            freq_y = float(params.get("freq_y", 0.9))
            omega_x = 2.0 * np.pi * freq_x
            omega_y = 2.0 * np.pi * freq_y

            x_true = x0 + amp_x * np.sin(omega_x * t)
            y_true = y0 + amp_y * np.cos(omega_y * t)
            vx_true = amp_x * omega_x * np.cos(omega_x * t)
            vy_true = -amp_y * omega_y * np.sin(omega_y * t)

        elif motion_type in ["accelerating", "ca"]:
            vx0 = float(params.get("vx0", 5.0))
            vy0 = float(params.get("vy0", 2.0))
            ax = float(params.get("ax", 30.0))
            ay = float(params.get("ay", 18.0))
            x_true = x0 + vx0 * t + 0.5 * ax * (t ** 2)
            y_true = y0 + vy0 * t + 0.5 * ay * (t ** 2)
            vx_true = vx0 + ax * t
            vy_true = vy0 + ay * t

        elif motion_type in ["camera_jitter", "jitter"]:
            vx = float(params.get("vx_px_per_sec", 30.0))
            vy = float(params.get("vy_px_per_sec", 15.0))
            jit_amp = float(params.get("jitter_amp", 15.0))
            x_base = x0 + vx * t
            y_base = y0 + vy * t
            x_true = x_base + rng.uniform(-jit_amp, jit_amp, size=num_frames)
            y_true = y_base + rng.uniform(-jit_amp, jit_amp, size=num_frames)
            vx_true.fill(vx)
            vy_true.fill(vy)

        elif motion_type in ["platform_motion", "platform_sway"]:
            vx = float(params.get("vx_px_per_sec", 25.0))
            vy = float(params.get("vy_px_per_sec", 12.0))
            sway_amp = float(params.get("sway_amp", 25.0))
            sway_freq = float(params.get("sway_freq", 0.7))
            omega_s = 2.0 * np.pi * sway_freq
            x_true = x0 + vx * t + sway_amp * np.sin(omega_s * t)
            y_true = y0 + vy * t + sway_amp * np.cos(omega_s * t)
            vx_true = vx + sway_amp * omega_s * np.cos(omega_s * t)
            vy_true = vy - sway_amp * omega_s * np.sin(omega_s * t)

        elif motion_type in ["fov_boundary_entry", "boundary_entry"]:
            x0_edge = float(params.get("x0", 35.0))
            y0_edge = float(params.get("y0", 35.0))
            vx = float(params.get("vx_px_per_sec", 45.0))
            vy = float(params.get("vy_px_per_sec", 35.0))
            x_true = x0_edge + vx * t
            y_true = y0_edge + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)

        elif motion_type in ["fov_exit_reentry", "occlusion_fade", "occlusion"]:
            x0_fade = float(params.get("x0", 120.0))
            y0_fade = float(params.get("y0", 180.0))
            vx = float(params.get("vx", 40.0))
            vy = float(params.get("vy", -15.0))
            x_true = x0_fade + vx * t
            y_true = y0_fade + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)

            fade_start = int(params.get("fade_start_frame", 40))
            fade_end = int(params.get("fade_end_frame", 65))
            for k in range(num_frames):
                if fade_start <= k < fade_end:
                    amplitude[k] = 0.0
                    is_occluded[k] = True

        elif motion_type in ["atmospheric_degradation", "low_snr"]:
            x0_haze = float(params.get("x0", 250.0))
            y0_haze = float(params.get("y0", 300.0))
            vx = float(params.get("vx_px_per_sec", 25.0))
            vy = float(params.get("vy_px_per_sec", 30.0))
            x_true = x0_haze + vx * t
            y_true = y0_haze + vy * t
            vx_true.fill(vx)
            vy_true.fill(vy)
            amplitude.fill(base_amplitude * 0.4)

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
