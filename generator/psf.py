import numpy as np

class PSFModel:
    """Base class for Point Spread Function (PSF) models."""
    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        raise NotImplementedError


class GaussianPSF(PSFModel):
    """
    2D Isotropic Gaussian PSF model:
    S(x, y) = A * exp(- (x - x0)^2 / (2 * sigma_x^2) - (y - y0)^2 / (2 * sigma_y^2))
    """
    def __init__(self, sigma_x: float = 2.0, sigma_y: float = 2.0):
        self.sigma_x = float(sigma_x)
        self.sigma_y = float(sigma_y)

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        if xx.ndim == 2 and yy.ndim == 2:
            x = xx[0, :]
            y = yy[:, 0]
            gx = np.exp(-0.5 * ((x - x0) / self.sigma_x) ** 2)
            gy = np.exp(-0.5 * ((y - y0) / self.sigma_y) ** 2)
            return amplitude * np.outer(gy, gx)
        term_x = ((xx - x0) ** 2) / (2.0 * self.sigma_x ** 2)
        term_y = ((yy - y0) ** 2) / (2.0 * self.sigma_y ** 2)
        return amplitude * np.exp(-(term_x + term_y))


class EllipticalGaussianPSF(PSFModel):
    """
    2D Anisotropic/Rotated Gaussian PSF model.
    """
    def __init__(self, sigma_x: float = 2.0, sigma_y: float = 3.0, theta_deg: float = 0.0):
        self.sigma_x = float(sigma_x)
        self.sigma_y = float(sigma_y)
        self.theta_deg = float(theta_deg)

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        theta = np.radians(self.theta_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        x_rot = cos_t * (xx - x0) + sin_t * (yy - y0)
        y_rot = -sin_t * (xx - x0) + cos_t * (yy - y0)

        term_x = (x_rot ** 2) / (2.0 * self.sigma_x ** 2)
        term_y = (y_rot ** 2) / (2.0 * self.sigma_y ** 2)
        return amplitude * np.exp(-(term_x + term_y))


class AsymmetricPSF(PSFModel):
    """
    Asymmetric PSF model:
    Weighted sum of a primary Gaussian component centered at (x0, y0) and a secondary
    displaced Gaussian component at (x0 + offset_x, y0 + offset_y) with relative amplitude alpha.
    S(x,y) = A * [ exp(-r1^2/(2*sigma^2)) + alpha * exp(-r2^2/(2*sigma^2)) ]
    """
    def __init__(self, sigma: float = 2.0, alpha: float = 0.2, offset_x: float = 1.0, offset_y: float = 0.0):
        self.sigma = float(sigma)
        self.alpha = float(alpha)
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        r1_sq = ((xx - x0) ** 2) + ((yy - y0) ** 2)
        g1 = np.exp(-r1_sq / (2.0 * self.sigma ** 2))

        x2 = x0 + self.offset_x
        y2 = y0 + self.offset_y
        r2_sq = ((xx - x2) ** 2) + ((yy - y2) ** 2)
        g2 = np.exp(-r2_sq / (2.0 * self.sigma ** 2))

        return amplitude * (g1 + self.alpha * g2)


class DefocusedPSF(PSFModel):
    """
    Defocused PSF model:
    Radially symmetric defocus blur approximation:
    sigma_eff^2 = sigma_nominal^2 + sigma_defocus^2
    """
    def __init__(self, sigma_nominal: float = 2.0, sigma_defocus: float = 0.0):
        self.sigma_nominal = float(sigma_nominal)
        self.sigma_defocus = float(sigma_defocus)
        self.sigma_eff = float(np.sqrt(self.sigma_nominal ** 2 + self.sigma_defocus ** 2))

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        term = ((xx - x0) ** 2 + (yy - y0) ** 2) / (2.0 * self.sigma_eff ** 2)
        return amplitude * np.exp(-term)


class AberratedPSF(PSFModel):
    """
    Aberrated PSF model:
    Modulates a 2D Gaussian core with optical coma and astigmatism wavefront distortions.
    S(x,y) = A * exp(-r^2/2) * max(0, 1 + W_coma * x_norm * r^2 + W_astig * (x_norm^2 - y_norm^2))
    """
    def __init__(self, sigma: float = 2.0, aberration_type: str = "coma", strength_waves: float = 0.1):
        self.sigma = float(sigma)
        self.aberration_type = str(aberration_type).lower()
        self.strength_waves = float(strength_waves)

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        x_norm = (xx - x0) / self.sigma
        y_norm = (yy - y0) / self.sigma
        r_sq = x_norm ** 2 + y_norm ** 2

        g_core = np.exp(-0.5 * r_sq)

        if "astig" in self.aberration_type:
            mod = 1.0 + self.strength_waves * (x_norm ** 2 - y_norm ** 2)
        else: # default coma
            mod = 1.0 + self.strength_waves * x_norm * r_sq

        mod_clipped = np.maximum(0.0, mod)
        return amplitude * g_core * mod_clipped


class TurbulentPSF(PSFModel):
    """
    Turbulent PSF model:
    Simulates atmospheric turbulence degradation (scintillation, beam broadening, speckle).
    Effective PSF width scales with turbulence strength (Cn2 / Fried parameter r0)
    and incorporates asymmetric speckle modulations.
    """
    def __init__(self, sigma_nominal: float = 2.0, cn2: float = 1e-14, r0_cm: float = 5.0, speckle_strength: float = 0.15):
        self.sigma_nominal = float(sigma_nominal)
        self.cn2 = float(cn2)
        self.r0_cm = float(r0_cm)
        self.speckle_strength = float(speckle_strength)
        # Broadening factor inversely proportional to r0
        self.sigma_turb = float(np.sqrt(self.sigma_nominal ** 2 + max(0.0, (10.0 / max(0.1, r0_cm)) - 1.0)))

    def render(self, xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, amplitude: float) -> np.ndarray:
        x_norm = (xx - x0) / self.sigma_turb
        y_norm = (yy - y0) / self.sigma_turb
        r_sq = x_norm ** 2 + y_norm ** 2

        g_core = np.exp(-0.5 * r_sq)
        # Add spatial speckle modulation representing phase screen turbulence effect
        speckle = 1.0 + self.speckle_strength * (np.cos(2.0 * x_norm) * np.sin(2.0 * y_norm) + 0.5 * np.cos(3.0 * y_norm))
        mod_clipped = np.maximum(0.0, speckle)
        return amplitude * g_core * mod_clipped


def get_psf_model(psf_type: str = "gaussian", **kwargs) -> PSFModel:
    """Factory function for instantiating PSF models from configuration parameters."""
    psf_type = str(psf_type).lower().strip()
    if psf_type in ["elliptical", "elliptical_gaussian"]:
        return EllipticalGaussianPSF(
            sigma_x=float(kwargs.get("sigma_x", kwargs.get("sigma", 2.0))),
            sigma_y=float(kwargs.get("sigma_y", kwargs.get("sigma", 2.0))),
            theta_deg=float(kwargs.get("theta_deg", kwargs.get("orientation_deg", 0.0)))
        )
    elif psf_type == "asymmetric":
        return AsymmetricPSF(
            sigma=float(kwargs.get("sigma", 2.0)),
            alpha=float(kwargs.get("alpha", kwargs.get("secondary_amplitude_ratio", 0.2))),
            offset_x=float(kwargs.get("offset_x", kwargs.get("secondary_offset_px", 1.0))),
            offset_y=float(kwargs.get("offset_y", 0.0))
        )
    elif psf_type == "defocused":
        return DefocusedPSF(
            sigma_nominal=float(kwargs.get("sigma_nominal", kwargs.get("sigma", 2.0))),
            sigma_defocus=float(kwargs.get("sigma_defocus", kwargs.get("blur_sigma_px", 0.0)))
        )
    elif psf_type in ["aberrated", "aberration"]:
        return AberratedPSF(
            sigma=float(kwargs.get("sigma", 2.0)),
            aberration_type=kwargs.get("aberration_type", "coma"),
            strength_waves=float(kwargs.get("strength_waves", 0.1))
        )
    elif psf_type in ["turbulence", "turbulent", "atmospheric_turbulence"]:
        return TurbulentPSF(
            sigma_nominal=float(kwargs.get("sigma_nominal", kwargs.get("sigma", 2.0))),
            cn2=float(kwargs.get("cn2", 1e-14)),
            r0_cm=float(kwargs.get("r0_cm", 5.0)),
            speckle_strength=float(kwargs.get("speckle_strength", 0.15))
        )
    else:
        return GaussianPSF(
            sigma_x=float(kwargs.get("sigma_x", kwargs.get("sigma", 2.0))),
            sigma_y=float(kwargs.get("sigma_y", kwargs.get("sigma", 2.0)))
        )

