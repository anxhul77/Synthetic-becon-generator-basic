import numpy as np

class AtmosphericModel:
    """
    Atmospheric attenuation model based on Beer-Lambert law:
    I_received = I_0 * exp(-alpha * L)
    
    Note: Currently models Beer-Lambert attenuation ONLY.
    Scattering, turbulence, fog, rain, and refraction are not implemented in baseline (condition is metadata).
    """
    def __init__(self, attenuation_alpha: float = 0.0001, range_km: float = 5.0, condition: str = "clear"):
        self.attenuation_alpha = float(attenuation_alpha)
        self.range_km = float(range_km)
        self.condition = str(condition)

    def calculate_transmittance(self) -> float:
        """Transmittance T = exp(-alpha * range_km)."""
        return float(np.exp(-self.attenuation_alpha * self.range_km))

    def apply_atmosphere(self, signal_amplitude: float) -> float:
        """Applies attenuation to peak signal amplitude."""
        transmittance = self.calculate_transmittance()
        return signal_amplitude * transmittance
