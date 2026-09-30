"""
Threshold-selection algorithms for FSOC beacon detection experiments.

Includes four primary approaches (8 total configurations):
1. Method A: Global (fixed) thresholding (T = 160.0 default)
2. Method B: Otsu histogram-based thresholding
3. Method C: Adaptive local thresholding (block_size = 31, offset C = 5.0)
4. Method D: Background mean plus k * std deviation (mu + k*sigma for k in [2, 3, 4, 5, 6])
"""
import time
import numpy as np
import cv2


def threshold_global(image: np.ndarray, threshold: float = 160.0, **kwargs) -> tuple[np.ndarray, dict]:
    """
    Method A: Global (fixed) thresholding.
    
    Foreground pixels satisfy I(x,y) > T_g.
    """
    img_arr = np.asarray(image)
    t0 = time.perf_counter()
    T_g = float(threshold)
    mask = (img_arr > T_g).astype(np.uint8)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    info = {
        "threshold_method": "global",
        "k": np.nan,
        "global_threshold": T_g,
        "selected_threshold": T_g,
        "background_mean": np.nan,
        "background_std": np.nan,
        "threshold_latency_ms": latency_ms
    }
    return mask, info


def threshold_otsu(image: np.ndarray, **kwargs) -> tuple[np.ndarray, dict]:
    """
    Method B: Otsu histogram-based thresholding.
    
    Calculates an optimal global threshold by maximizing between-class variance.
    Handles degenerate/constant images safely.
    """
    img_arr = np.asarray(image)
    if img_arr.dtype != np.uint8:
        img_uint8 = np.clip(img_arr, 0, 255).astype(np.uint8)
    else:
        img_uint8 = img_arr

    t0 = time.perf_counter()
    min_val, max_val = int(np.min(img_uint8)), int(np.max(img_uint8))
    if min_val == max_val:
        # Constant / degenerate image
        selected_T = float(max_val)
        mask = np.zeros_like(img_uint8, dtype=np.uint8)
    else:
        otsu_val, mask = cv2.threshold(img_uint8, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        selected_T = float(otsu_val)

    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    info = {
        "threshold_method": "otsu",
        "k": np.nan,
        "global_threshold": np.nan,
        "selected_threshold": selected_T,
        "background_mean": np.nan,
        "background_std": np.nan,
        "threshold_latency_ms": latency_ms
    }
    return mask.astype(np.uint8), info


def threshold_adaptive(image: np.ndarray, block_size: int = 31, C: float = 5.0, **kwargs) -> tuple[np.ndarray, dict]:
    """
    Method C: Local adaptive mean thresholding.
    
    Threshold map T(x,y) = mu_W(x,y) - C.
    Foreground pixels satisfy I(x,y) > T(x,y).
    Uses BORDER_REPLICATE border handling.
    """
    img_arr = np.asarray(image)
    if img_arr.dtype != np.uint8:
        img_uint8 = np.clip(img_arr, 0, 255).astype(np.uint8)
    else:
        img_uint8 = img_arr

    # Ensure odd block size >= 3
    b_size = int(block_size)
    if b_size % 2 == 0:
        b_size += 1
    b_size = max(3, b_size)

    t0 = time.perf_counter()
    # OpenCV cv2.adaptiveThreshold computes T(x,y) = mean(W) - C
    # and sets output to 255 where I(x,y) > T(x,y).
    mask_255 = cv2.adaptiveThreshold(
        img_uint8,
        maxValue=1,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=b_size,
        C=float(C)
    )
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    info = {
        "threshold_method": "adaptive",
        "k": np.nan,
        "global_threshold": np.nan,
        "selected_threshold": np.nan,  # Spatially varying
        "background_mean": np.nan,
        "background_std": np.nan,
        "threshold_latency_ms": latency_ms
    }
    return mask_255.astype(np.uint8), info


def threshold_mu_plus_k_sigma(image: np.ndarray, k: float = 3.0,
                             bg_mean: float = None, bg_std: float = None, **kwargs) -> tuple[np.ndarray, dict]:
    """
    Method D: Background mean plus multiple of standard deviation (mu + k * sigma).
    
    Global threshold T = mu_B + k * sigma_B derived from estimated background statistics.
    Background statistics are estimated across the image frame without using ground-truth beacon location.
    """
    img_arr = np.asarray(image, dtype=np.float64)

    t0 = time.perf_counter()
    if bg_mean is None or bg_std is None:
        mu_B = float(np.mean(img_arr))
        sigma_B = float(np.std(img_arr))
    else:
        mu_B = float(bg_mean)
        sigma_B = float(bg_std)

    k_val = float(k)
    T = mu_B + k_val * sigma_B
    mask = (img_arr > T).astype(np.uint8)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    method_name = f"mu_plus_{int(k_val) if k_val.is_integer() else k_val}sigma"

    info = {
        "threshold_method": method_name,
        "k": k_val,
        "global_threshold": np.nan,
        "selected_threshold": T,
        "background_mean": mu_B,
        "background_std": sigma_B,
        "threshold_latency_ms": latency_ms
    }
    return mask, info


# Registry mapping method names to (function, default_params) pairs.
THRESHOLD_REGISTRY = {
    "global": (threshold_global, {"threshold": 160.0}),
    "otsu": (threshold_otsu, {}),
    "adaptive": (threshold_adaptive, {"block_size": 31, "C": 5.0}),
    "mu_plus_2sigma": (threshold_mu_plus_k_sigma, {"k": 2.0}),
    "mu_plus_3sigma": (threshold_mu_plus_k_sigma, {"k": 3.0}),
    "mu_plus_4sigma": (threshold_mu_plus_k_sigma, {"k": 4.0}),
    "mu_plus_5sigma": (threshold_mu_plus_k_sigma, {"k": 5.0}),
    "mu_plus_6sigma": (threshold_mu_plus_k_sigma, {"k": 6.0}),
}


def get_thresholding_method(method: str, params: dict = None):
    """
    Returns (threshold_function, merged_params) for the given threshold method name.
    """
    if method not in THRESHOLD_REGISTRY:
        raise ValueError(f"Unknown thresholding method: {method}. "
                         f"Available: {list(THRESHOLD_REGISTRY.keys())}")
    fn, defaults = THRESHOLD_REGISTRY[method]
    merged = dict(defaults)
    if params:
        merged.update(params)
    return fn, merged
