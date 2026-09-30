"""
Background suppression filters for FSOC beacon detection experiments.

Includes:
1. Method A: None (Pass-through baseline)
2. Method B: Gaussian background estimation & subtraction
3. Method C: Morphological white top-hat filtering
"""
import numpy as np
import cv2


def apply_none(image: np.ndarray, **kwargs) -> np.ndarray:
    """Method A: Pass-through baseline (no background suppression)."""
    return image


def apply_gaussian_sub(image: np.ndarray, sigma: float = 15.0, **kwargs) -> np.ndarray:
    """
    Method B: Gaussian background estimation and subtraction.
    
    1. Estimate slowly varying background B_hat using 2D Gaussian blur.
    2. Subtract estimated background from original image.
    3. Retain positive residual max(0, I - B_hat).
    """
    img_float = image.astype(np.float64)
    # Calculate odd kernel size >= 6 * sigma + 1
    ksize = int(np.ceil(6.0 * sigma))
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    b_hat = cv2.GaussianBlur(img_float, (ksize, ksize), sigma, borderType=cv2.BORDER_REFLECT)
    residual = img_float - b_hat
    positive_residual = np.maximum(0.0, residual)
    return np.clip(positive_residual, 0, 255).astype(np.uint8)


def apply_tophat(image: np.ndarray, radius: int = 7, **kwargs) -> np.ndarray:
    """
    Method C: Morphological white top-hat filtering.
    
    I_tophat = I - (I o S)
    Uses a circular/elliptical structuring element S with specified radius.
    """
    d = 2 * int(radius) + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d))
    return cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)


# Registry mapping method names to (function, default_params) pairs.
SUPPRESSION_REGISTRY = {
    "none": (apply_none, {}),
    "gaussian_sub": (apply_gaussian_sub, {"sigma": 15.0}),
    "tophat": (apply_tophat, {"radius": 7}),
}


def get_suppression_filter(method: str, params: dict = None):
    """
    Returns (filter_function, merged_params) for the given suppression method name.
    Custom params override defaults.
    """
    if method not in SUPPRESSION_REGISTRY:
        raise ValueError(f"Unknown background suppression method: {method}. "
                         f"Available: {list(SUPPRESSION_REGISTRY.keys())}")
    fn, defaults = SUPPRESSION_REGISTRY[method]
    merged = dict(defaults)
    if params:
        merged.update(params)
    return fn, merged
