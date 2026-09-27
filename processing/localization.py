import numpy as np
from scipy.optimize import curve_fit

def intensity_weighted_centroid(image: np.ndarray, roi_bbox: tuple = None) -> tuple[float, float]:
    """
    Computes intensity-weighted centroid:
    x_hat = sum(x * I(x,y)) / sum(I(x,y))
    y_hat = sum(y * I(x,y)) / sum(I(x,y))
    """
    if roi_bbox is not None:
        xmin, ymin, xmax, ymax = roi_bbox
        sub_img = image[ymin:ymax, xmin:xmax].astype(np.float64)
        off_x, off_y = xmin, ymin
    else:
        # Auto-crop ROI around peak intensity location
        max_idx = np.unravel_index(np.argmax(image), image.shape)
        cy_max, cx_max = max_idx
        win_r = 15
        ymin = max(0, cy_max - win_r)
        ymax = min(image.shape[0], cy_max + win_r + 1)
        xmin = max(0, cx_max - win_r)
        xmax = min(image.shape[1], cx_max + win_r + 1)
        sub_img = image[ymin:ymax, xmin:xmax].astype(np.float64)
        off_x, off_y = xmin, ymin

    # Subtract background baseline before computing weighted centroid
    bg_baseline = np.min(sub_img)
    sub_img_clean = np.maximum(0.0, sub_img - bg_baseline)

    total_intensity = np.sum(sub_img_clean)
    if total_intensity <= 0:
        h, w = sub_img.shape
        return off_x + w / 2.0, off_y + h / 2.0

    height, width = sub_img.shape
    x_coords = np.arange(width, dtype=np.float64)
    y_coords = np.arange(height, dtype=np.float64)
    xx, yy = np.meshgrid(x_coords, y_coords)

    x_hat = np.sum(xx * sub_img_clean) / total_intensity + off_x
    y_hat = np.sum(yy * sub_img_clean) / total_intensity + off_y

    return float(x_hat), float(y_hat)


def gaussian_2d_func(coords, amplitude, x0, y0, sigma_x, sigma_y, bg):
    x, y = coords
    term_x = ((x - x0) ** 2) / (2.0 * sigma_x ** 2)
    term_y = ((y - y0) ** 2) / (2.0 * sigma_y ** 2)
    return (bg + amplitude * np.exp(-(term_x + term_y))).ravel()


def gaussian_fit_localization(image: np.ndarray, roi_bbox: tuple = None) -> tuple[float, float]:
    """
    Fits a 2D Gaussian function to the image region to extract subpixel location (x0, y0).
    """
    if roi_bbox is not None:
        xmin, ymin, xmax, ymax = roi_bbox
        sub_img = image[ymin:ymax, xmin:xmax].astype(np.float64)
        off_x, off_y = xmin, ymin
    else:
        # Find peak intensity location and extract window
        max_idx = np.unravel_index(np.argmax(image), image.shape)
        cy_max, cx_max = max_idx
        win_r = 15
        ymin = max(0, cy_max - win_r)
        ymax = min(image.shape[0], cy_max + win_r + 1)
        xmin = max(0, cx_max - win_r)
        xmax = min(image.shape[1], cx_max + win_r + 1)
        sub_img = image[ymin:ymax, xmin:xmax].astype(np.float64)
        off_x, off_y = xmin, ymin

    height, width = sub_img.shape
    x_coords = np.arange(width, dtype=np.float64)
    y_coords = np.arange(height, dtype=np.float64)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # Initial parameter estimates
    bg_init = np.min(sub_img)
    amp_init = np.max(sub_img) - bg_init
    xc_init, yc_init = intensity_weighted_centroid(sub_img)

    p0 = [amp_init, xc_init, yc_init, 2.0, 2.0, bg_init]
    bounds = (
        [0.0, 0.0, 0.0, 0.1, 0.1, 0.0],
        [np.inf, width, height, width, height, np.inf]
    )

    try:
        popt, _ = curve_fit(
            gaussian_2d_func,
            (xx, yy),
            sub_img.ravel(),
            p0=p0,
            bounds=bounds,
            maxfev=1000
        )
        x_fit = popt[1] + off_x
        y_fit = popt[2] + off_y
        return float(x_fit), float(y_fit)
    except Exception:
        # Fallback to intensity-weighted centroid if curve fit fails
        xc, yc = intensity_weighted_centroid(sub_img)
        return xc + off_x, yc + off_y
