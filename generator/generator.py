import uuid
import numpy as np
from .camera import PinholeCamera
from .psf import GaussianPSF, EllipticalGaussianPSF, PSFModel, get_psf_model
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
                       psf_model_instance: PSFModel = None,
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
                       bit_depth: int = 8,
                       beacon_present: bool = True,
                       distractors: list[dict] = None,
                       noise_reference_amplitude: float = None,
                       **kwargs) -> tuple[np.ndarray, dict]:
        
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

        # 2. PSF Selection & Signal Generation
        if psf_model_instance is not None:
            psf_model = psf_model_instance
        else:
            psf_model = get_psf_model(psf_type=psf_type, sigma_x=sigma_x, sigma_y=sigma_y, **kwargs)

        if beacon_present:
            beacon = BeaconSignal(x0=x0, y0=y0, amplitude=attenuated_amplitude, psf_model=psf_model)
            signal = beacon.render(self.camera.width, self.camera.height)
        else:
            signal = np.zeros((self.camera.height, self.camera.width), dtype=np.float64)

        # Render false bright distractors if provided
        distractor_gt_list = []
        if distractors is not None:
            for dist in distractors:
                dx0 = float(dist.get("x0", 960.0))
                dy0 = float(dist.get("y0", 540.0))
                d_amp = float(dist.get("amplitude", 150.0))
                d_sig_x = float(dist.get("sigma_x", 2.0))
                d_sig_y = float(dist.get("sigma_y", 2.0))
                d_psf_type = dist.get("psf_type", "gaussian")
                d_attenuated_amp = atmo.apply_atmosphere(d_amp)
                if d_psf_type == "elliptical":
                    d_psf = EllipticalGaussianPSF(sigma_x=d_sig_x, sigma_y=d_sig_y, theta_deg=0.0)
                else:
                    d_psf = GaussianPSF(sigma_x=d_sig_x, sigma_y=d_sig_y)
                d_beacon = BeaconSignal(x0=dx0, y0=dy0, amplitude=d_attenuated_amp, psf_model=d_psf)
                signal = signal + d_beacon.render(self.camera.width, self.camera.height)
                distractor_gt_list.append({
                    "x0": dx0, "y0": dy0, "amplitude": d_amp,
                    "sigma_x": d_sig_x, "sigma_y": d_sig_y, "psf_type": d_psf_type
                })

        # 3. Background Generation
        g_change = kwargs.get("gradient_change", 100.0)
        if background_type in ["gradient", "horizontal", "horizontal_gradient", "vertical", "vertical_gradient", "two_dimensional", "2d_gradient"]:
            if background_type in ["horizontal", "horizontal_gradient"]:
                g_a = gradient_a if gradient_a != 0.0 else g_change / max(1, self.camera.width - 1)
                g_b = 0.0
            elif background_type in ["vertical", "vertical_gradient"]:
                g_a = 0.0
                g_b = gradient_b if gradient_b != 0.0 else g_change / max(1, self.camera.height - 1)
            elif background_type in ["two_dimensional", "2d_gradient"]:
                g_a = gradient_a if gradient_a != 0.0 else g_change / max(1, self.camera.width - 1)
                g_b = gradient_b if gradient_b != 0.0 else g_change / max(1, self.camera.height - 1)
            else:
                g_a = gradient_a
                g_b = gradient_b
            bg_model = GradientBackground(baseline=background_level, a=g_a, b=g_b)
        else:
            bg_model = UniformBackground(baseline=background_level)

        background = bg_model.render(self.camera.width, self.camera.height)

        # 4. Noiseless Image
        noiseless_image = signal + background

        # 5. Sensor Noise Addition
        noise_ref_amp = (attenuated_amplitude if noise_reference_amplitude is None
                         else float(noise_reference_amplitude))
        if noise_ref_amp < 0.0:
            raise ValueError("noise_reference_amplitude must be non-negative")
        noise_model = GaussianNoise(snr_db=snr_db, amplitude=noise_ref_amp)
        noisy_image, sigma_n = noise_model.add_noise(noiseless_image, rng)

        # 6. Quantization / Clipping to Image uint8 or float format
        max_val = (2 ** bit_depth) - 1 if bit_depth < 64 else np.inf
        if bit_depth < 64:
            clipped_image = np.clip(noisy_image, 0, max_val)
        else:
            clipped_image = noisy_image

        if bit_depth == 8:
            synthetic_image = clipped_image.astype(np.uint8)
        else:
            synthetic_image = clipped_image.astype(np.float32)

        # 7. Angular Ground-Truth Calculation
        if beacon_present:
            theta_x_true, theta_y_true = self.camera.pixel_to_angle(x0, y0)
        else:
            theta_x_true, theta_y_true = None, None

        ground_truth = {
            "image_id": image_id,
            "seed": seed,
            "generator_version": self.generator_version,
            "width": self.camera.width,
            "height": self.camera.height,
            "beacon_present": bool(beacon_present),
            "x_true": float(x0) if beacon_present else None,
            "y_true": float(y0) if beacon_present else None,
            "phi_x": float(x0 - np.floor(x0)) if beacon_present else None,
            "phi_y": float(y0 - np.floor(y0)) if beacon_present else None,
            "theta_x_true": float(theta_x_true) if theta_x_true is not None else None,
            "theta_y_true": float(theta_y_true) if theta_y_true is not None else None,
            "amplitude": float(amplitude),
            "attenuated_amplitude": float(attenuated_amplitude),
            "background": float(background_level),
            "background_type": background_type,
            "sigma_x": float(sigma_x),
            "sigma_y": float(sigma_y),
            "snr_db": float(snr_db),
            "sigma_n": float(sigma_n),
            "noise_reference_amplitude": float(noise_ref_amp),
            "received_snr_db": (float(20.0 * np.log10(attenuated_amplitude / sigma_n))
                                 if attenuated_amplitude > 0.0 and sigma_n > 0.0 else None),
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
            "cy": float(self.camera.cy),
            "distractors": distractor_gt_list
        }

        return synthetic_image, ground_truth
