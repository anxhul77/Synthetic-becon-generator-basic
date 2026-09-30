import numpy as np

def calculate_fixed_energy_amplitude(
    sigma: float,
    amplitude_ref: float = 150.0,
    sigma_ref: float = 2.0
) -> float:
    """
    Calculates beacon peak amplitude required to keep total integrated signal energy constant
    across varying PSF standard deviations (sigma).

    Continuous 2D Gaussian integrated energy above background:
    E = 2 * pi * A * sigma^2

    Setting E(sigma) = E(sigma_ref) yields:
    A(sigma) = A_ref * (sigma_ref^2 / sigma^2)
    """
    sigma = float(sigma)
    if sigma <= 0.0:
        raise ValueError(f"PSF sigma must be strictly positive, got {sigma}")
    return float(amplitude_ref * (float(sigma_ref) ** 2) / (sigma ** 2))


def measure_rendered_signal_energy(
    image: np.ndarray,
    background_level: float,
    roi_mask: np.ndarray = None
) -> float:
    """
    Measures the empirical integrated signal energy above background from a rendered frame or ROI.
    """
    signal_above_bg = np.maximum(0.0, image.astype(np.float64) - float(background_level))
    if roi_mask is not None:
        signal_above_bg = signal_above_bg * roi_mask
    return float(np.sum(signal_above_bg))
