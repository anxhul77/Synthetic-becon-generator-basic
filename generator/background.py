import numpy as np

class BackgroundModel:
    """Base class for background illumination."""
    def render(self, width: int, height: int) -> np.ndarray:
        raise NotImplementedError

class UniformBackground(BackgroundModel):
    """Uniform background illumination B(x, y) = B0."""
    def __init__(self, baseline: float = 10.0):
        self.baseline = float(baseline)

    def render(self, width: int, height: int) -> np.ndarray:
        return np.full((height, width), self.baseline, dtype=np.float64)

class GradientBackground(BackgroundModel):
    """Linear gradient background illumination B(x, y) = B0 + a*x + b*y."""
    def __init__(self, baseline: float = 10.0, a: float = 0.01, b: float = 0.005):
        self.baseline = float(baseline)
        self.a = float(a)
        self.b = float(b)

    def render(self, width: int, height: int) -> np.ndarray:
        x = np.arange(width, dtype=np.float64)
        y = np.arange(height, dtype=np.float64)
        radiance = self.baseline + (self.a * x)[None, :] + (self.b * y)[:, None]
        return np.maximum(0.0, radiance)
