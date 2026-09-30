import time
import numpy as np
from scipy.ndimage import label, center_of_mass
from typing import Dict, Any, List, Tuple, Optional

class FullFrameBeaconDetector:
    """
    Full-Frame Classical Beacon Detector.
    Performs full-frame thresholding, connected component segmentation,
    candidate centroid extraction, and candidate selection against ground truth matching gate.
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
        5. Matches candidates to ground truth location (if beacon_present=True)
        """
        start_time = time.perf_counter()

        bg_mean = float(np.mean(image))
        bg_std = float(np.std(image))
        threshold = bg_mean + self.k_thresh * bg_std

        binary_mask = image > threshold
        labeled_mask, num_features = label(binary_mask)

        candidates = []
        if num_features > 0:
            for i in range(1, num_features + 1):
                component_mask = (labeled_mask == i)
                area = int(np.sum(component_mask))
                if self.min_area <= area <= self.max_area:
                    # Center of mass of blob
                    cy, cx = center_of_mass(image, labeled_mask, i)
                    candidates.append({
                        "id": i,
                        "x_cx": float(cx),
                        "y_cy": float(cy),
                        "area": area,
                        "peak_val": float(np.max(image[component_mask]))
                    })

        detected_beacon = None
        is_detected = False
        is_false_alarm = False
        min_dist = np.inf

        if beacon_present and x_gt is not None and y_gt is not None:
            # Find candidate closest to true beacon location within matching gate
            for cand in candidates:
                dist = float(np.sqrt((cand["x_cx"] - x_gt)**2 + (cand["y_cy"] - y_gt)**2))
                if dist <= self.match_tol and dist < min_dist:
                    min_dist = dist
                    detected_beacon = cand
                    is_detected = True
        else:
            # Beacon absent frame: any candidate detected is a false alarm
            if len(candidates) > 0:
                is_false_alarm = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "threshold": threshold,
            "num_raw_blobs": num_features,
            "num_candidates": len(candidates),
            "candidates": candidates,
            "is_detected": is_detected,
            "is_false_alarm": is_false_alarm,
            "matched_candidate": detected_beacon,
            "matched_dist_px": min_dist if is_detected else None,
            "latency_ms": elapsed_ms
        }
