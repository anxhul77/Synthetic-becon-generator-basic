import numpy as np
import cv2
from scipy import ndimage
from processing.localization import intensity_weighted_centroid

class ClassicalBeaconDetector:
    """
    Classical Baseline Optical Beacon Detector Pipeline.
    
    1. Numerical Representation: Accepts monochrome image (uint8 or float64).
    2. Global Thresholding: Applies fixed global threshold rule T (e.g. T = 160.0 on raw image,
       equivalent to threshold 60.0 above background baseline 100.0).
    3. Connected Component Labeling: 8-connected component extraction.
    4. Candidate Selection: Non-ML candidate selection rule based on peak intensity (I_max).
    5. Centroid Estimation: Subpixel location estimation via intensity-weighted centroid on primary candidate.
    """
    def __init__(self, threshold: float = 160.0, min_area: int = 1):
        self.threshold = float(threshold)
        self.min_area = int(min_area)

    def detect(self, image: np.ndarray, beacon_gt: tuple[float, float] = None, tolerance_px: float = 5.0, binary_mask: np.ndarray = None) -> dict:
        """
        Processes a monochrome image frame and extracts candidate components and primary beacon estimate.
        
        If binary_mask is provided, component extraction is performed on binary_mask, while
        intensity measurements and centroid calculations use the original image.
        """
        import time
        img_arr = np.asarray(image)

        # 1. Thresholding (if binary_mask not provided)
        t_comp0 = time.perf_counter()
        if binary_mask is not None:
            binary = (binary_mask > 0).astype(np.uint8)
        else:
            binary = (img_arr > self.threshold).astype(np.uint8)

        # 2. Connected Component Labeling
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
        t_comp1 = time.perf_counter()
        component_latency_ms = (t_comp1 - t_comp0) * 1000.0

        # Label 0 is background; candidates are 1..num_labels-1
        if num_labels <= 1:
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "component_latency_ms": component_latency_ms,
                "localization_latency_ms": 0.0
            }

        cand_indices = np.arange(1, num_labels)
        areas = stats[cand_indices, cv2.CC_STAT_AREA]

        valid_mask = areas >= self.min_area
        if not np.any(valid_mask):
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "component_latency_ms": component_latency_ms,
                "localization_latency_ms": 0.0
            }

        valid_indices = cand_indices[valid_mask]
        valid_stats = stats[valid_indices]
        valid_centroids = centroids[valid_indices]
        num_cand = len(valid_indices)

        # 3. Peak Intensity & Integrated Intensity for Candidates
        peaks = ndimage.maximum(img_arr, labels, index=valid_indices)
        sums = ndimage.sum_labels(img_arr, labels, index=valid_indices)

        # 4. Select by image evidence only. Ground truth, when supplied, is
        # used below solely for post-hoc scoring and never for selection.
        best_i = int(np.lexsort((sums, peaks))[-1])

        x_box = int(valid_stats[best_i, cv2.CC_STAT_LEFT])
        y_box = int(valid_stats[best_i, cv2.CC_STAT_TOP])
        w_box = int(valid_stats[best_i, cv2.CC_STAT_WIDTH])
        h_box = int(valid_stats[best_i, cv2.CC_STAT_HEIGHT])
        bbox = (x_box, y_box, x_box + w_box, y_box + h_box)

        # 5. Centroid Estimation: Intensity-weighted centroid over primary candidate ROI
        t_loc0 = time.perf_counter()
        xc, yc = intensity_weighted_centroid(img_arr, roi_bbox=bbox)
        t_loc1 = time.perf_counter()
        localization_latency_ms = (t_loc1 - t_loc0) * 1000.0

        best_cand = {
            "label": int(valid_indices[best_i]),
            "bbox": bbox,
            "area": int(valid_stats[best_i, cv2.CC_STAT_AREA]),
            "peak": float(peaks[best_i]),
            "sum": float(sums[best_i]),
            "x_est": float(xc),
            "y_est": float(yc)
        }

        # Preserve all candidates for honest false-candidate accounting and
        # diagnostics. Secondary candidates retain component centroids; only
        # the selected candidate receives the subpixel weighted centroid.
        candidates = []
        for i, label_id in enumerate(valid_indices):
            left = int(valid_stats[i, cv2.CC_STAT_LEFT])
            top = int(valid_stats[i, cv2.CC_STAT_TOP])
            width = int(valid_stats[i, cv2.CC_STAT_WIDTH])
            height = int(valid_stats[i, cv2.CC_STAT_HEIGHT])
            candidates.append({
                "label": int(label_id),
                "bbox": (left, top, left + width, top + height),
                "area": int(valid_stats[i, cv2.CC_STAT_AREA]),
                "peak": float(peaks[i]),
                "sum": float(sums[i]),
                "x_est": float(valid_centroids[i, 0]),
                "y_est": float(valid_centroids[i, 1]),
                "is_primary": bool(i == best_i),
            })

        # Vectorized candidate classification relative to ground truth (if provided)
        matching_count = 0
        false_candidate_count = num_cand
        if beacon_gt is not None:
            bx, by = beacon_gt
            dists = np.sqrt((valid_centroids[:, 0] - bx) ** 2 + (valid_centroids[:, 1] - by) ** 2)
            matching_mask = dists <= tolerance_px
            matching_count = int(np.sum(matching_mask))
            false_candidate_count = int(num_cand - matching_count)

        return {
            "detected": True,
            "x_est": best_cand["x_est"],
            "y_est": best_cand["y_est"],
            "num_candidates": num_cand,
            "matching_count": matching_count,
            "false_candidate_count": false_candidate_count,
            "primary_candidate": best_cand,
            "candidates": candidates,
            "component_latency_ms": component_latency_ms,
            "localization_latency_ms": localization_latency_ms
        }
