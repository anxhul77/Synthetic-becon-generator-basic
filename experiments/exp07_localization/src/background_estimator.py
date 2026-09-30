import numpy as np

def estimate_border_background(roi_image: np.ndarray, border_width: int = 2) -> tuple[float, float]:
    """
    Estimates mean and standard deviation of background using the outer border of the ROI.
    Guarantees no ground truth information is used.
    """
    h, w = roi_image.shape
    bw = min(border_width, h // 4, w // 4)
    bw = max(1, bw)

    mask = np.ones((h, w), dtype=bool)
    mask[bw:h-bw, bw:w-bw] = False

    border_pixels = roi_image[mask]
    if len(border_pixels) == 0:
        return float(np.min(roi_image)), 0.0

    bg_mean = float(np.mean(border_pixels))
    bg_std = float(np.std(border_pixels))
    return bg_mean, bg_std

def estimate_gradient_background(roi_image: np.ndarray, border_width: int = 2) -> tuple[float, float, float]:
    """
    Fits a 2D linear background model B(x, y) = B0 + a*x + b*y to outer border pixels of ROI.
    Returns (B0, a, b).
    """
    h, w = roi_image.shape
    bw = min(border_width, h // 4, w // 4)
    bw = max(1, bw)

    mask = np.ones((h, w), dtype=bool)
    mask[bw:h-bw, bw:w-bw] = False

    y_coords, x_coords = np.nonzero(mask)
    z_vals = roi_image[mask]

    # Least squares solve for [B0, a, b]
    A = np.column_stack([np.ones_like(x_coords), x_coords, y_coords])
    try:
        popt, _, _, _ = np.linalg.lstsq(A, z_vals, rcond=None)
        return float(popt[0]), float(popt[1]), float(popt[2])
    except Exception:
        return float(np.mean(z_vals)), 0.0, 0.0
