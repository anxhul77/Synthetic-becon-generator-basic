import numpy as np
from typing import Dict, Any, Tuple
from generator.atmosphere import AtmosphericModel

class ExtendedAtmosphericModel:
    """
    Comprehensive FSOC Atmospheric Propagation Model combining:
    1. Beer-Lambert Transmission Attenuation: T(L) = exp(-alpha * L)
    2. Atmospheric Turbulence: Scintillation (amplitude fluctuation), Beam Wander (position jitter), Spot Broadening
    3. Atmospheric Scattering: Spatial Energy Redistribution Halo (1 - eta)*Direct + eta*Halo
    """
    def __init__(
        self,
        attenuation_alpha: float = 0.0001,
        range_km: float = 5.0,
        turbulence_strength: float = 0.0,
        scattering_fraction: float = 0.0,
        halo_sigma: float = 10.0
    ):
        self.attenuation_alpha = float(attenuation_alpha)
        self.range_km = float(range_km)
        self.turbulence_strength = float(turbulence_strength)
        self.scattering_fraction = float(np.clip(scattering_fraction, 0.0, 0.95))
        self.halo_sigma = float(halo_sigma)
        self.base_atmo = AtmosphericModel(attenuation_alpha=attenuation_alpha, range_km=range_km)

    def calculate_transmittance(self) -> float:
        """Returns Beer-Lambert transmittance T(L) = exp(-alpha * L)."""
        return self.base_atmo.calculate_transmittance()

    def apply_attenuation(self, initial_amplitude: float) -> float:
        """Applies attenuation to peak amplitude."""
        return self.base_atmo.apply_atmosphere(initial_amplitude)

    def apply_turbulence(
        self,
        x0: float,
        y0: float,
        amplitude: float,
        sigma_0: float,
        rng: np.random.Generator
    ) -> Tuple[float, float, float, float]:
        """
        Applies turbulence perturbations:
        1. Irradiance scintillation: A_turb = A * max(0, 1 + sigma_I * w_scint)
        2. Beam wander displacement: (x_turb, y_turb) = (x0 + dx, y0 + dy)
        3. Spot broadening: sigma_eff = sqrt(sigma_0^2 + sigma_blur^2)

        Returns: (x_turb, y_turb, amp_turb, sigma_eff)
        """
        if self.turbulence_strength <= 0.0:
            return float(x0), float(y0), float(amplitude), float(sigma_0)

        # Scintillation index scaling
        sigma_I = 0.25 * self.turbulence_strength
        w_scint = rng.normal(0.0, 1.0)
        amp_turb = max(0.0, amplitude * (1.0 + sigma_I * w_scint))

        # Beam wander std dev (pixels)
        sigma_wander = 2.5 * self.turbulence_strength
        dx = rng.normal(0.0, sigma_wander)
        dy = rng.normal(0.0, sigma_wander)
        x_turb = x0 + dx
        y_turb = y0 + dy

        # Spot broadening
        sigma_blur = 1.5 * self.turbulence_strength
        sigma_eff = float(np.sqrt(sigma_0**2 + sigma_blur**2))

        return float(x_turb), float(y_turb), float(amp_turb), sigma_eff

    def apply_scattering_halo(
        self,
        direct_signal: np.ndarray,
        x0: float,
        y0: float,
        total_energy: float
    ) -> np.ndarray:
        """
        Applies atmospheric scattering energy redistribution:
        I_scattered = (1 - eta) * I_direct + eta * I_halo
        where I_halo is a normalized wide Gaussian halo centered at beacon position (x0, y0).
        """
        eta = self.scattering_fraction
        if eta <= 0.0:
            return direct_signal

        h, w = direct_signal.shape
        yy, xx = np.ogrid[:h, :w]
        r_sq = (xx - x0)**2 + (yy - y0)**2

        # Normalized Gaussian halo
        halo_kernel = np.exp(-r_sq / (2.0 * self.halo_sigma**2))
        halo_norm = halo_kernel / np.sum(halo_kernel)

        direct_energy = np.sum(direct_signal)
        halo_signal = halo_norm * direct_energy

        scattered_signal = (1.0 - eta) * direct_signal + eta * halo_signal
        return scattered_signal
