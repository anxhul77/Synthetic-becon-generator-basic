"""
Connected-Component Feature Extraction and Filtering Modules for FSOC Beacon Detection.

Provides feature extraction for binary connected components and modular filtering
strategies based on shape, area, circularity, aspect ratio, and peak intensity.
"""

import time
import numpy as np
import cv2
from scipy import ndimage


def extract_component_features(image: np.ndarray, binary_mask: np.ndarray) -> list[dict]:
    """
    Extracts geometric and intensity features for all 8-connected components in binary_mask.

    Vectorized implementation for ultra-fast processing across high component count noise frames.

    Parameters
    ----------
    image : np.ndarray
        Original monochrome uint8 or float image (for intensity measurements).
    binary_mask : np.ndarray
        Binary mask (uint8, non-zero values represent foreground).

    Returns
    -------
    list[dict]
        List of component feature dictionaries containing:
        label, area, bbox, width, height, aspect_ratio, perimeter,
        circularity, peak_intensity, mean_intensity, centroid, solidity, fill_ratio.
    """
    img_arr = np.asarray(image)
    mask_uint8 = (binary_mask > 0).astype(np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_uint8, connectivity=8)

    if num_labels <= 1:
        return []

    cand_indices = np.arange(1, num_labels)
    num_cand = len(cand_indices)

    # Bulk extraction of intensity statistics
    peaks = ndimage.maximum(img_arr, labels, index=cand_indices)
    sums = ndimage.sum_labels(img_arr, labels, index=cand_indices)

    # Bulk extraction of geometric statistics
    lefts = stats[cand_indices, cv2.CC_STAT_LEFT]
    tops = stats[cand_indices, cv2.CC_STAT_TOP]
    widths = stats[cand_indices, cv2.CC_STAT_WIDTH]
    heights = stats[cand_indices, cv2.CC_STAT_HEIGHT]
    areas = stats[cand_indices, cv2.CC_STAT_AREA]

    cx = centroids[cand_indices, 0]
    cy = centroids[cand_indices, 1]

    min_dims = np.minimum(widths, heights)
    max_dims = np.maximum(widths, heights)
    aspect_ratios = np.where(min_dims > 0, max_dims / min_dims, 1.0)

    bbox_areas = widths * heights
    fill_ratios = np.where(bbox_areas > 0, areas / bbox_areas, 1.0)
    means = np.where(areas > 0, sums / areas, 0.0)

    # Pre-allocated arrays for contour-derived geometric features
    perimeters = np.zeros(num_cand, dtype=np.float64)
    circularities = np.zeros(num_cand, dtype=np.float64)
    solidities = np.zeros(num_cand, dtype=np.float64)

    # Vectorized fast-paths for common small shapes (area 1, area 2, filled rectangles)
    mask_area1 = (areas == 1)
    if np.any(mask_area1):
        perimeters[mask_area1] = 4.0
        circularities[mask_area1] = float((4.0 * np.pi) / 16.0)
        solidities[mask_area1] = 1.0

    mask_area2 = (areas == 2)
    if np.any(mask_area2):
        perimeters[mask_area2] = 6.0
        circularities[mask_area2] = float((8.0 * np.pi) / 36.0)
        solidities[mask_area2] = 1.0

    mask_rect = (bbox_areas == areas) & (~mask_area1) & (~mask_area2)
    if np.any(mask_rect):
        p_rect = 2.0 * (widths[mask_rect] + heights[mask_rect])
        perimeters[mask_rect] = p_rect
        circularities[mask_rect] = np.where(p_rect > 0, (4.0 * np.pi * areas[mask_rect]) / (p_rect * p_rect), 0.0)
        solidities[mask_rect] = 1.0

    # Complex components requiring contour extraction
    complex_mask = (~mask_area1) & (~mask_area2) & (~mask_rect)
    complex_indices = np.where(complex_mask)[0]

    if len(complex_indices) > 0:
        for idx in complex_indices:
            label_id = int(cand_indices[idx])
            left = int(lefts[idx])
            top = int(tops[idx])
            w = int(widths[idx])
            h = int(heights[idx])
            area = int(areas[idx])

            crop_labels = labels[top:top + h, left:left + w]
            comp_crop = (crop_labels == label_id).astype(np.uint8)
            padded_crop = np.pad(comp_crop, pad_width=1, mode='constant', constant_values=0)
            contours, _ = cv2.findContours(padded_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            if contours:
                cnt = contours[0]
                perim = float(cv2.arcLength(cnt, closed=True))
                perimeters[idx] = perim
                if perim > 0:
                    circularities[idx] = float((4.0 * np.pi * area) / (perim * perim))

                hull = cv2.convexHull(cnt)
                hull_area = float(cv2.contourArea(hull))
                if hull_area > 0:
                    solidities[idx] = float(area / hull_area)

    # Fast construction of feature dict list
    features = [
        {
            "label": int(cand_indices[i]),
            "area": int(areas[i]),
            "bbox": (int(lefts[i]), int(tops[i]), int(lefts[i] + widths[i]), int(tops[i] + heights[i])),
            "width": int(widths[i]),
            "height": int(heights[i]),
            "aspect_ratio": float(aspect_ratios[i]),
            "perimeter": float(perimeters[i]),
            "circularity": float(circularities[i]),
            "peak_intensity": float(peaks[i]),
            "mean_intensity": float(means[i]),
            "sum_intensity": float(sums[i]),
            "centroid": (float(cx[i]), float(cy[i])),
            "solidity": float(solidities[i]),
            "fill_ratio": float(fill_ratios[i]),
        }
        for i in range(num_cand)
    ]

    return features


def filter_none(components: list[dict], **kwargs) -> list[dict]:
    """Baseline filter. Returns all components unmodified."""
    return list(components)


def filter_min_area(components: list[dict], min_area: int = 3, **kwargs) -> list[dict]:
    """Filters out components with area strictly less than min_area."""
    m_area = int(min_area)
    return [c for c in components if c["area"] >= m_area]


def filter_max_area(components: list[dict], max_area: int = 50, **kwargs) -> list[dict]:
    """Filters out components with area strictly greater than max_area."""
    m_area = int(max_area)
    return [c for c in components if c["area"] <= m_area]


def filter_aspect_ratio(components: list[dict], max_aspect_ratio: float = 2.0, **kwargs) -> list[dict]:
    """Filters out elongated components with aspect ratio > max_aspect_ratio."""
    max_ar = float(max_aspect_ratio)
    return [c for c in components if c["aspect_ratio"] <= max_ar]


def filter_circularity(components: list[dict], min_circularity: float = 0.5, **kwargs) -> list[dict]:
    """Filters out non-circular components with circularity < min_circularity."""
    min_c = float(min_circularity)
    return [c for c in components if c["circularity"] >= min_c]


def filter_peak_intensity(components: list[dict], min_peak_intensity: float = 180.0, **kwargs) -> list[dict]:
    """Filters out low-contrast components with peak intensity < min_peak_intensity."""
    min_peak = float(min_peak_intensity)
    return [c for c in components if c["peak_intensity"] >= min_peak]


def filter_combined(components: list[dict], min_area: int = 3, max_area: int = 50,
                    max_aspect_ratio: float = 2.0, min_circularity: float = 0.5,
                    min_peak_intensity: float = 180.0, **kwargs) -> list[dict]:
    """
    Combined multi-criterion component filter applying min area, max area,
    aspect ratio, circularity, and peak intensity thresholds simultaneously.
    """
    m_min_area = int(min_area)
    m_max_area = int(max_area)
    max_ar = float(max_aspect_ratio)
    min_c = float(min_circularity)
    min_peak = float(min_peak_intensity)

    filtered = []
    for c in components:
        if c["area"] < m_min_area or c["area"] > m_max_area:
            continue
        if c["aspect_ratio"] > max_ar:
            continue
        if c["circularity"] < min_c:
            continue
        if c["peak_intensity"] < min_peak:
            continue
        filtered.append(c)
    return filtered


COMPONENT_FILTER_REGISTRY = {
    "none": (filter_none, {}),
    "min_area": (filter_min_area, {"min_area": 3}),
    "max_area": (filter_max_area, {"max_area": 50}),
    "aspect_ratio": (filter_aspect_ratio, {"max_aspect_ratio": 2.0}),
    "circularity": (filter_circularity, {"min_circularity": 0.5}),
    "peak_intensity": (filter_peak_intensity, {"min_peak_intensity": 180.0}),
    "combined": (filter_combined, {
        "min_area": 3,
        "max_area": 50,
        "max_aspect_ratio": 2.0,
        "min_circularity": 0.5,
        "min_peak_intensity": 180.0
    })
}


def get_component_filter(method: str, params: dict = None):
    """
    Returns (filter_function, merged_params) for the given component filter method.
    Custom params override defaults.
    """
    if method not in COMPONENT_FILTER_REGISTRY:
        raise ValueError(f"Unknown component filter method: {method}. "
                         f"Available: {list(COMPONENT_FILTER_REGISTRY.keys())}")
    fn, defaults = COMPONENT_FILTER_REGISTRY[method]
    merged = dict(defaults)
    if params:
        merged.update(params)
    return fn, merged
