import numpy as np
from .psf import PSFModel, GaussianPSF

class BeaconSignal:
    """
    Represents an optical beacon signal rendered on a grid via a PSF model.
    """
    def __init__(self, x0: float, y0: float, amplitude: float = 150.0, psf_model: PSFModel = None):
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.amplitude = float(amplitude)
        self.psf_model = psf_model if psf_model is not None else GaussianPSF()

    def render(self, width: int, height: int) -> np.ndarray:
        x = np.arange(width, dtype=np.float64)
        y = np.arange(height, dtype=np.float64)
        xx, yy = np.meshgrid(x, y)
        return self.psf_model.render(xx, yy, self.x0, self.y0, self.amplitude)
