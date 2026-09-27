"""
Extension Points / Future physical effect interfaces for FSOC Synthetic Beacon Image Generator.

These interfaces define the expansion architecture for future phases.
They are NOT currently active in the validated baseline generator (v1.0.0).
"""

import numpy as np

class FutureExtensionError(NotImplementedError):
    """Raised when an un-implemented physical effect extension point is called."""
    pass

class BaseTurbulenceModel:
    """Extension point for atmospheric turbulence (scintillation, beam wander, phase distortion)."""
    def apply_turbulence(self, image: np.ndarray, Cn2: float, L_km: float) -> np.ndarray:
        raise FutureExtensionError("Atmospheric turbulence model is not yet implemented in baseline v1.0.0.")

class BaseScatteringModel:
    """Extension point for aerosol / fog / rain scattering models."""
    def apply_scattering(self, image: np.ndarray, visibility_km: float, weather_condition: str) -> np.ndarray:
        raise FutureExtensionError("Atmospheric scattering model is not yet implemented in baseline v1.0.0.")

class BaseJitterModel:
    """Extension point for high-frequency angular camera jitter / vibration."""
    def apply_jitter(self, theta_x: float, theta_y: float, jitter_sigma_rad: float) -> tuple[float, float]:
        raise FutureExtensionError("Camera jitter model is not yet implemented in baseline v1.0.0.")

class BasePlatformMotionModel:
    """Extension point for platform dynamics and low-frequency drift."""
    def compute_position(self, t: float) -> tuple[float, float, float]:
        raise FutureExtensionError("Platform motion model is not yet implemented in baseline v1.0.0.")

class BasePoissonNoiseModel:
    """Extension point for photon shot noise / Poisson noise physics."""
    def add_shot_noise(self, image: np.ndarray, gain: float) -> np.ndarray:
        raise FutureExtensionError("Poisson noise model is not yet implemented in baseline v1.0.0.")

class BaseImpulseNoiseModel:
    """Extension point for salt-and-pepper / dead-and-hot pixel sensor noise."""
    def add_impulse_noise(self, image: np.ndarray, p_salt: float, p_pepper: float) -> np.ndarray:
        raise FutureExtensionError("Impulse noise model is not yet implemented in baseline v1.0.0.")

class BaseMultiTargetGenerator:
    """Extension point for multiple moving optical targets and false bright clutter."""
    def render_scene(self, targets: list[dict], clutter: list[dict]) -> np.ndarray:
        raise FutureExtensionError("Multi-target / clutter rendering is not yet implemented in baseline v1.0.0.")
