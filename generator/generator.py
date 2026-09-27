import uuid
import numpy as np
from .camera import PinholeCamera
from .psf import GaussianPSF, EllipticalGaussianPSF
from .beacon import BeaconSignal
from .background import UniformBackground, GradientBackground
from .noise import GaussianNoise
from .atmosphere import AtmosphericModel

class SyntheticBeaconGenerator:
    """
    Ground-truth Synthetic Beacon Image Generator.
    Models the physical image formation pipeline:
      Beacon ground truth -> Atmospheric attenuation -> Optical PSF -> Background -> Sensor noise -> Clipping/Quantization -> Synthetic image
    Returns both synthetic_image (uint8 / float64) and complete ground_truth dictionary.
    """
    generator_version: str = "1.0.0"

    def __init__(self, camera: PinholeCamera = None):
        self.camera = camera if camera is not None else PinholeCamera()

    def generate_frame(self,
                       x0: float = 960.0,
                       y0: float = 540.0,
                       amplitude: float = 150.0,
                       sigma_x: float = 2.0,
                       sigma_y: float = 2.0,
                       psf_type: str = "gaussian",
                       background_type: str = "uniform",
                       background_level: float = 10.0,
                       gradient_a: float = 0.0,
                       gradient_b: float = 0.0,
                       snr_db: float = 30.0,
                       range_km: float = 5.0,
                       attenuation_alpha: float = 0.0001,
                       atmospheric_condition: str = "clear",
                       seed: int = None,
                       image_id: str = None,
                       bit_depth: int = 8) -> tuple[np.ndarray, dict]:
        
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()
            seed = int(rng.integers(0, 1e9))

        if image_id is None:
            image_id = str(uuid.uuid4())

        # 1. Atmospheric Attenuation
        atmo = AtmosphericModel(attenuation_alpha=attenuation_alpha, range_km=range_km, condition=atmospheric_condition)
        attenuated_amplitude = atmo.apply_atmosphere(amplitude)

        # 2. PSF Selection & Beacon Signal Generation
        if psf_type == "elliptical":
            psf_model = EllipticalGaussianPSF(sigma_x=sigma_x, sigma_y=sigma_y, theta_deg=0.0)
        else:
            psf_model = GaussianPSF(sigma_x=sigma_x, sigma_y=sigma_y)

        beacon = BeaconSignal(x0=x0, y0=y0, amplitude=attenuated_amplitude, psf_model=psf_model)
        signal = beacon.render(self.camera.width, self.camera.height)

        # 3. Background Generation
        if background_type == "gradient":
            bg_model = GradientBackground(baseline=background_level, a=gradient_a, b=gradient_b)
        else:
            bg_model = UniformBackground(baseline=background_level)

        background = bg_model.render(self.camera.width, self.camera.height)

        # 4. Noiseless Image
        noiseless_image = signal + background

        # 5. Sensor Noise Addition
        noise_model = GaussianNoise(snr_db=snr_db, amplitude=attenuated_amplitude)
        noisy_image, sigma_n = noise_model.add_noise(noiseless_image, rng)

        # 6. Quantization / Clipping to Image uint8 or float format
        max_val = (2 ** bit_depth) - 1 if bit_depth < 64 else np.inf
        if bit_depth < 64:
            clipped_image = np.clip(noisy_image, 0, max_val)
        else:
            clipped_image = noisy_image

        if bit_depth == 8:
            synthetic_image = np.round(clipped_image).astype(np.uint8)
        else:
            synthetic_image = clipped_image.astype(np.float64)

        # 7. Angular Ground-Truth Calculation
        theta_x_true, theta_y_true = self.camera.pixel_to_angle(x0, y0)

        ground_truth = {
            "image_id": image_id,
            "seed": seed,
            "generator_version": self.generator_version,
            "width": self.camera.width,
            "height": self.camera.height,
            "x_true": float(x0),
            "y_true": float(y0),
            "theta_x_true": float(theta_x_true),
            "theta_y_true": float(theta_y_true),
            "amplitude": float(amplitude),
            "attenuated_amplitude": float(attenuated_amplitude),
            "background": float(background_level),
            "background_type": background_type,
            "sigma_x": float(sigma_x),
            "sigma_y": float(sigma_y),
            "snr_db": float(snr_db),
            "sigma_n": float(sigma_n),
            "psf_type": psf_type,
            "noise_type": "gaussian",
            "range_km": float(range_km),
            "attenuation_alpha": float(attenuation_alpha),
            "atmospheric_condition": atmospheric_condition,
            "transmittance": float(atmo.calculate_transmittance()),
            "camera_fps": float(self.camera.fps),
            "fx": float(self.camera.fx),
            "fy": float(self.camera.fy),
            "cx": float(self.camera.cx),
            "cy": float(self.camera.cy)
        }

        return synthetic_image, ground_truth
