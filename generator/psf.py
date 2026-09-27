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
