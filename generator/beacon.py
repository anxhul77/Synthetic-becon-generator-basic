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
        out = np.zeros((height, width), dtype=np.float32)
        radius = 35
        x_min = max(0, int(np.floor(self.x0 - radius)))
        x_max = min(width, int(np.ceil(self.x0 + radius + 1)))
        y_min = max(0, int(np.floor(self.y0 - radius)))
        y_max = min(height, int(np.ceil(self.y0 + radius + 1)))
        if x_min >= x_max or y_min >= y_max:
            return out
        x = np.arange(x_min, x_max, dtype=np.float32)
        y = np.arange(y_min, y_max, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)
        out[y_min:y_max, x_min:x_max] = self.psf_model.render(xx, yy, self.x0, self.y0, self.amplitude)
        return out
