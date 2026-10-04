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
        noise = rng.normal(0.0, std, size=image.shape).astype(np.float32)
        noisy_image = image + noise
        return noisy_image, std


class PoissonNoise(NoiseModel):
    """
    Poisson shot noise model where pixel intensities represent photon counts.
    I_noisy ~ Poisson(max(0, I_noiseless) * scale) / scale
    """
    def __init__(self, scale: float = 1.0):
        self.scale = float(scale)

    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
        scale = max(1e-6, self.scale)
        scaled_img = np.maximum(0.0, image * scale)
        noisy_scaled = rng.poisson(scaled_img)
        noisy_image = noisy_scaled.astype(np.float64) / scale
        variance = float(np.mean(scaled_img)) / (scale ** 2)
        equiv_sigma = float(np.sqrt(max(0.0, variance)))
        return noisy_image, equiv_sigma


class SaltAndPepperNoise(NoiseModel):
    """
    Salt-and-Pepper impulse noise model.
    Randomly replaces a specified ratio of pixels with min_val (pepper) or max_val (salt).
    """
    def __init__(self, noise_ratio: float = 0.10, salt_vs_pepper: float = 0.5, max_val: float = 255.0):
        self.noise_ratio = float(noise_ratio)
        self.salt_vs_pepper = float(salt_vs_pepper)
        self.max_val = float(max_val)

    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
        if self.noise_ratio <= 0.0:
            return image.copy(), 0.0
        
        noisy_image = image.copy()
        h, w = image.shape
        num_noisy = int(np.round(self.noise_ratio * h * w))
        
        if num_noisy > 0:
            flat_indices = rng.choice(h * w, size=num_noisy, replace=False)
            num_salt = int(np.round(self.salt_vs_pepper * num_noisy))
            salt_indices = flat_indices[:num_salt]
            pepper_indices = flat_indices[num_salt:]
            
            y_salt, x_salt = np.unravel_index(salt_indices, (h, w))
            y_pep, x_pep = np.unravel_index(pepper_indices, (h, w))
            
            noisy_image[y_salt, x_salt] = self.max_val
            noisy_image[y_pep, x_pep] = 0.0

        return noisy_image, self.noise_ratio * self.max_val


class CombinedNoiseModel(NoiseModel):
    """
    Combines Gaussian AWGN, Poisson shot noise, and Salt-and-Pepper impulse noise.
    """
    def __init__(self, gaussian_snr_db: float = 20.0,
                 amplitude: float = 150.0,
                 enable_poisson: bool = False,
                 poisson_scale: float = 1.0,
                 sp_noise_ratio: float = 0.0,
                 max_val: float = 255.0):
        self.gaussian = GaussianNoise(snr_db=gaussian_snr_db, amplitude=amplitude) if gaussian_snr_db is not None else None
        self.enable_poisson = enable_poisson
        self.poisson = PoissonNoise(scale=poisson_scale) if enable_poisson else None
        self.sp_noise_ratio = sp_noise_ratio
        self.salt_pepper = SaltAndPepperNoise(noise_ratio=sp_noise_ratio, max_val=max_val) if sp_noise_ratio > 0 else None

    def add_noise(self, image: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
        current_img = image.copy()
        effective_sigma_sq = 0.0

        # 1. Poisson noise
        if self.enable_poisson and self.poisson is not None:
            current_img, sig_p = self.poisson.add_noise(current_img, rng)
            effective_sigma_sq += sig_p ** 2

        # 2. Gaussian AWGN
        if self.gaussian is not None:
            current_img, sig_g = self.gaussian.add_noise(current_img, rng)
            effective_sigma_sq += sig_g ** 2

        # 3. Salt & Pepper impulse noise
        if self.salt_pepper is not None:
            current_img, sig_sp = self.salt_pepper.add_noise(current_img, rng)
            effective_sigma_sq += sig_sp ** 2

        return current_img, float(np.sqrt(effective_sigma_sq))

