"""
Modular image denoising filters for FSOC beacon detection experiments.

Each filter accepts a uint8 monochrome image and returns a uint8 monochrome image
of identical shape. Filter parameters are configurable and documented.
"""
import numpy as np
import cv2


def apply_none(image: np.ndarray, **kwargs) -> np.ndarray:
    """No-filter baseline. Returns the original image unchanged."""
    return image


def apply_gaussian(image: np.ndarray, ksize: int = 5, sigma: float = 1.0, **kwargs) -> np.ndarray:
    """
    Gaussian blur filter.

    Parameters
    ----------
    ksize : int
        Kernel size (must be odd and positive). Default 5 (approx 2.5× PSF sigma=2).
    sigma : float
        Gaussian standard deviation. Default 1.0 (half of PSF sigma to avoid
        excessive beacon blurring).
    """
    return cv2.GaussianBlur(image, (ksize, ksize), sigma)


def apply_median(image: np.ndarray, ksize: int = 3, **kwargs) -> np.ndarray:
    """
    Median filter.

    Parameters
    ----------
    ksize : int
        Kernel size (must be odd). Default 3 (smallest useful kernel, avoids
        distorting the 2-pixel-sigma beacon PSF).
    """
    return cv2.medianBlur(image, ksize)


def apply_bilateral(image: np.ndarray, d: int = 5, sigma_color: float = 30.0,
                     sigma_space: float = 2.0, **kwargs) -> np.ndarray:
    """
    Bilateral filter (edge-preserving denoising).

    Parameters
    ----------
    d : int
        Diameter of the pixel neighbourhood. Default 5.
    sigma_color : float
        Filter sigma in the colour (intensity) space. Default 30.0
        (moderate for uint8 range 0-255).
    sigma_space : float
        Filter sigma in the coordinate space. Default 2.0
        (matched to PSF sigma to preserve beacon shape).
    """
    return cv2.bilateralFilter(image, d, sigma_color, sigma_space)


# Registry mapping method names to (function, default_params) pairs.
FILTER_REGISTRY = {
    "none":      (apply_none, {}),
    "gaussian":  (apply_gaussian, {"ksize": 5, "sigma": 1.0}),
    "median":    (apply_median, {"ksize": 3}),
    "bilateral": (apply_bilateral, {"d": 5, "sigma_color": 30.0, "sigma_space": 2.0}),
}


def get_filter(method: str, params: dict = None):
    """
    Returns (filter_function, merged_params) for the given method name.
    Custom params override the defaults.
    """
    if method not in FILTER_REGISTRY:
        raise ValueError(f"Unknown filter method: {method}. "
                         f"Available: {list(FILTER_REGISTRY.keys())}")
    fn, defaults = FILTER_REGISTRY[method]
    merged = dict(defaults)
    if params:
        merged.update(params)
    return fn, merged
