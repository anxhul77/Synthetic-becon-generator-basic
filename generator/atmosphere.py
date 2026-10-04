"""
Physical Traceable FSOC Atmospheric Propagation & Link Model.

Models:
1. Kruse/Kim Mie Scattering & Attenuation: gamma(lambda, V) = (3.91 / V) * (lambda / 550 nm)^(-q)
2. Marshall-Palmer Rain Attenuation: gamma_rain = a * R^b
3. Rytov Turbulence & Fried Parameter r0: Cn2, sigma_R^2, beam wander jitter, and scintillation
4. Spatial Energy Redistribution Scattering Halo: (1 - eta) * I_direct + eta * I_halo
5. Physical Atmospheric Scenarios: Clear, Haze, Fog, Rain, Low Light, Turbulence, Scattering Halo
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional


def kruse_attenuation_alpha(wavelength_nm: float, visibility_km: float) -> float:
    """
    Calculates atmospheric attenuation coefficient gamma (km^-1) using Kruse/Kim visibility model:
    gamma(lambda, V) = (3.91 / V) * (lambda / 550.0)^(-q)
    """
    V = float(max(0.01, visibility_km))
    lam = float(wavelength_nm)

    if V > 50.0:
        q = 1.6
    elif V > 6.0:
        q = 1.3
    elif V > 1.0:
        q = 0.585 * (V ** (1.0 / 3.0))
    else:
        q = 0.0  # Dense fog / Mie limit

    gamma = (3.91 / V) * ((lam / 550.0) ** (-q))
    return float(gamma)


def rain_attenuation_alpha(rain_rate_mm_hr: float) -> float:
    """Calculates rain attenuation coefficient gamma_rain (km^-1) via Marshall-Palmer model."""
    R = float(max(0.0, rain_rate_mm_hr))
    if R <= 0.0:
        return 0.0
    return float(0.35 * (R ** 0.63))


class AtmosphericModel:
    """
    Physical FSOC Atmospheric Propagation Model with traceable parameters.
    """
    SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
        "clear": {
            "visibility_km": 23.0,
            "attenuation_alpha_km": None, # Computed via Kruse
            "turbulence_cn2": 1e-15,
            "scattering_fraction": 0.01,
            "rain_rate_mm_hr": 0.0,
            "background_level": 10.0,
            "description": "Clear atmosphere (Visibility = 23 km, low turbulence, minimal scattering)"
        },
        "haze": {
            "visibility_km": 5.0,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 5e-14,
            "scattering_fraction": 0.15,
            "rain_rate_mm_hr": 0.0,
            "background_level": 15.0,
            "description": "Moderate Haze (Visibility = 5 km, moderate scattering)"
        },
        "fog": {
            "visibility_km": 1.5,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 1e-14,
            "scattering_fraction": 0.40,
            "rain_rate_mm_hr": 0.0,
            "background_level": 20.0,
            "description": "Light Fog (Visibility = 1.5 km, heavy attenuation and scattering)"
        },
        "rain": {
            "visibility_km": 4.0,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 2e-14,
            "scattering_fraction": 0.20,
            "rain_rate_mm_hr": 5.0, # 5 mm/hr rain
            "background_level": 12.0,
            "description": "Moderate Rain (Rain rate = 5 mm/hr, droplets scattering)"
        },
        "low_light": {
            "visibility_km": 20.0,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 1e-15,
            "scattering_fraction": 0.02,
            "rain_rate_mm_hr": 0.0,
            "background_level": 2.0, # Low ambient background radiance
            "description": "Low Light / Night Condition (Low background noise baseline)"
        },
        "turbulence": {
            "visibility_km": 20.0,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 1e-13, # Strong turbulence
            "scattering_fraction": 0.05,
            "rain_rate_mm_hr": 0.0,
            "background_level": 10.0,
            "description": "Strong Turbulence & Beam Wander (Cn2 = 1e-13 m^-2/3)"
        },
        "scattering_halo": {
            "visibility_km": 10.0,
            "attenuation_alpha_km": None,
            "turbulence_cn2": 1e-14,
            "scattering_fraction": 0.35, # Heavy halo energy redistribution
            "rain_rate_mm_hr": 0.0,
            "background_level": 15.0,
            "description": "Scattering Halo (35% optical energy redistributed into spatial halo)"
        }
    }

    def __init__(
        self,
        wavelength_nm: float = 1550.0,
        visibility_km: float = 23.0,
        attenuation_alpha: Optional[float] = None,
        range_km: float = 5.0,
        turbulence_cn2: float = 1e-15,
        scattering_fraction: float = 0.01,
        rain_rate_mm_hr: float = 0.0,
        condition: str = "clear"
    ):
        self.wavelength_nm = float(wavelength_nm)
        self.condition = str(condition).lower().strip()
        self.range_km = float(range_km)

        # Load preset defaults if condition matches preset
        if self.condition in self.SCENARIO_PRESETS:
            preset = self.SCENARIO_PRESETS[self.condition]
            self.visibility_km = float(preset["visibility_km"])
            self.turbulence_cn2 = float(preset["turbulence_cn2"])
            self.scattering_fraction = float(preset["scattering_fraction"])
            self.rain_rate_mm_hr = float(preset["rain_rate_mm_hr"])
        else:
            self.visibility_km = float(visibility_km)
            self.turbulence_cn2 = float(turbulence_cn2)
            self.scattering_fraction = float(scattering_fraction)
            self.rain_rate_mm_hr = float(rain_rate_mm_hr)

        # Calculate total atmospheric attenuation coefficient gamma (km^-1)
        if attenuation_alpha is not None:
            self.attenuation_alpha_km = float(attenuation_alpha)
        else:
            gamma_kruse = kruse_attenuation_alpha(self.wavelength_nm, self.visibility_km)
            gamma_rain = rain_attenuation_alpha(self.rain_rate_mm_hr)
            self.attenuation_alpha_km = float(gamma_kruse + gamma_rain)

    def calculate_transmittance(self) -> float:
        """Beer-Lambert Transmittance T(L) = exp(-gamma_km * range_km)."""
        return float(np.exp(-self.attenuation_alpha_km * self.range_km))

    def apply_atmosphere(self, signal_amplitude: float) -> float:
        """Applies Beer-Lambert attenuation to peak signal amplitude."""
        return float(signal_amplitude * self.calculate_transmittance())

    def calculate_rytov_variance(self) -> float:
        """Calculates Rytov variance for spherical wave scintillation: sigma_R^2 = 0.563 * k^(7/6) * Cn2 * L^(11/6)."""
        k = 2.0 * np.pi / (self.wavelength_nm * 1e-9)
        L_m = self.range_km * 1000.0
        return float(0.563 * (k ** (7.0 / 6.0)) * self.turbulence_cn2 * (L_m ** (11.0 / 6.0)))

    def calculate_beam_wander_std_px(self, focal_length_px: float = 2000.0) -> float:
        """Estimates beam wander displacement jitter in pixels."""
        if self.turbulence_cn2 <= 0:
            return 0.0
        # Angular jitter variance sigma_theta^2 ~ 2.91 * Cn2 * L * D^(-1/3)
        L_m = self.range_km * 1000.0
        sigma_ang_rad = np.sqrt(max(0.0, 2.91 * self.turbulence_cn2 * L_m * (0.05 ** (-1.0 / 3.0))))
        return float(sigma_ang_rad * focal_length_px)
