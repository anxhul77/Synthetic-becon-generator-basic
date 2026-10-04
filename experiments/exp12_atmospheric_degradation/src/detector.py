import time
import numpy as np
from scipy.ndimage import label, center_of_mass
from typing import Dict, Any, List, Tuple, Optional

class FullFrameBeaconDetector:
    """
    Full-Frame Classical Beacon Detector.
    Performs full-frame thresholding, connected component segmentation,
    candidate centroid extraction, and image-only candidate selection. Ground
    truth is accepted only for post-hoc scoring and never selects a candidate.
    """
    def __init__(
        self,
        threshold_multiplier: float = 3.5,
        min_area_px: int = 3,
        max_area_px: int = 500,
        matching_tolerance_px: float = 5.0
    ):
        self.k_thresh = threshold_multiplier
        self.min_area = min_area_px
        self.max_area = max_area_px
        self.match_tol = matching_tolerance_px

    def detect(
        self,
        image: np.ndarray,
        x_gt: Optional[float] = None,
        y_gt: Optional[float] = None,
        beacon_present: bool = True
    ) -> Dict[str, Any]:
        """
        Executes full-frame detection:
        1. Computes global noise/background threshold T = bg_mean + k * bg_std
        2. Binarizes image
        3. Extracts connected components
        4. Calculates centroids of candidate blobs
        5. Selects the strongest candidate without ground truth. If ground
           truth is supplied, reports whether that selected candidate matches.
        """
        start_time = time.perf_counter()

        bg_mean = float(np.mean(image))
        bg_std = float(np.std(image))
        threshold = bg_mean + self.k_thresh * bg_std

        binary_mask = image > threshold
        candidates = []
        if num_features > 0:
            from scipy.ndimage import find_objects
            slices = find_objects(labeled_mask)
            for i, sl in enumerate(slices, start=1):
                if sl is None:
                    continue
                sub_labeled = labeled_mask[sl]
                sub_img = image[sl]
                mask = (sub_labeled == i)
                area = int(np.sum(mask))
                if self.min_area <= area <= self.max_area:
                    cy_sub, cx_sub = center_of_mass(sub_img, sub_labeled, i)
                    cx = sl[1].start + cx_sub
                    cy = sl[0].start + cy_sub
                    candidates.append({
                        "id": i,
                        "x_cx": float(cx),
                        "y_cy": float(cy),
                        "area": area,
                        "peak_val": float(np.max(sub_img[mask]))
                    })

        detected_beacon = None
        is_detected = False
        is_false_alarm = False
        min_dist = np.inf

        if candidates:
            # Image-only selection: highest peak, then largest area.
            detected_beacon = max(candidates, key=lambda c: (c["peak_val"], c["area"]))
            if beacon_present and x_gt is not None and y_gt is not None:
                min_dist = float(np.hypot(detected_beacon["x_cx"] - x_gt,
                                          detected_beacon["y_cy"] - y_gt))
                is_detected = bool(min_dist <= self.match_tol)
            else:
                is_false_alarm = True

        declared_detection = bool(detected_beacon is not None)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "threshold": threshold,
            "num_raw_blobs": num_features,
            "num_candidates": len(candidates),
            "candidates": candidates,
            "is_detected": is_detected,
            "declared_detection": declared_detection,
            "is_false_alarm": is_false_alarm,
            "matched_candidate": detected_beacon,
            "matched_dist_px": min_dist if is_detected else None,
            "latency_ms": elapsed_ms
        }
