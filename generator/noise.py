import numpy as np

class NoiseModel:
    """Base class for noise models."""
    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
        raise NotImplementedError

class GaussianNoise(NoiseModel):
    """
    Gaussian noise N ~ N(0, sigma_n^2).
    SNR in dB defines noise standard deviation relative to peak signal amplitude A:
    SNR_dB = 20 * log10(A / sigma_n)  =>  sigma_n = A * 10^(-SNR_dB / 20)
    """
    def __init__(self, snr_db: float = 30.0, amplitude: float = 150.0):
        self.snr_db = float(snr_db)
        self.amplitude = float(amplitude)

    @property
    def sigma_n(self) -> float:
        if self.snr_db >= 100.0:
            return 0.0
        return self.amplitude * (10.0 ** (-self.snr_db / 20.0))

    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
        std = self.sigma_n
        if std <= 0.0:
            return image.copy(), 0.0
        noise = rng.normal(0.0, std, size=image.shape)
        noisy_image = image + noise
        return noisy_image, std
