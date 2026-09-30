import time
import numpy as np
import cv2
from processing.detector import ClassicalBeaconDetector
from processing.component_filtering import get_component_filter, extract_component_features
from .ai_detector import AIBeaconDetector

class HybridBeaconDetector:
    """
    Hybrid Beacon Detector.
    Fuses outputs from Classical Detector and AI Detector using deterministic spatial matching.
    """
    def __init__(self,
                 classical_detector: ClassicalBeaconDetector = None,
                 ai_detector: AIBeaconDetector = None,
                 matching_radius_px: float = 5.0,
                 weight_classical: float = 0.5):
        
        if classical_detector is None:
            # Baseline classical detector with Exp 05 combined filter
            self.classical_detector = ClassicalBeaconDetector(threshold=160.0, min_area=3)
        else:
            self.classical_detector = classical_detector

        if ai_detector is None:
            self.ai_detector = AIBeaconDetector()
        else:
            self.ai_detector = ai_detector

        self.matching_radius_px = float(matching_radius_px)
        self.w_class = float(weight_classical)
        self.w_ai = 1.0 - self.w_class

        # Component filter function from Exp 05
        filter_fn, _ = get_component_filter("combined", {
            "min_area": 3, "max_area": 50, "max_aspect_ratio": 2.0,
            "min_circularity": 0.5, "min_peak_intensity": 180.0
        })
        self.combined_filter_fn = filter_fn

    def fuse_results(self, class_res: dict, ai_res: dict, frame: np.ndarray = None) -> dict:
        """
        Performs spatial candidate fusion given classical and AI detector outputs.
        """
        class_detected = class_res["detected"] and class_res["x_est"] is not None
        ai_detected = ai_res["detected"] and ai_res["x_est"] is not None

        fused_x, fused_y = None, None
        fused_detected = False
        fusion_status = "none"

        if class_detected and ai_detected:
            cx, cy = float(class_res["x_est"]), float(class_res["y_est"])
            ax, ay = float(ai_res["x_est"]), float(ai_res["y_est"])
            dist = np.sqrt((cx - ax) ** 2 + (cy - ay) ** 2)

            if dist <= self.matching_radius_px:
                fused_x = self.w_class * cx + self.w_ai * ax
                fused_y = self.w_class * cy + self.w_ai * ay
                fused_detected = True
                fusion_status = "spatial_match"
            else:
                if float(ai_res.get("confidence", 0.0)) >= 0.7:
                    fused_x, fused_y = ax, ay
                    fusion_status = "ai_priority"
                else:
                    fused_x, fused_y = cx, cy
                    fusion_status = "classical_priority"
                fused_detected = True

        elif class_detected and not ai_detected:
            fused_x, fused_y = float(class_res["x_est"]), float(class_res["y_est"])
            fused_detected = True
            fusion_status = "classical_fallback"

        elif ai_detected and not class_detected:
            fused_x, fused_y = float(ai_res["x_est"]), float(ai_res["y_est"])
            fused_detected = True
            fusion_status = "ai_fallback"

        primary_cand = None
        if fused_detected:
            primary_cand = {
                "x_est": fused_x,
                "y_est": fused_y,
                "fusion_status": fusion_status
            }

        return {
            "detected": fused_detected,
            "x_est": fused_x,
            "y_est": fused_y,
            "num_candidates": 1 if fused_detected else 0,
            "primary_candidate": primary_cand,
            "candidates": [primary_cand] if fused_detected else [],
            "fusion_status": fusion_status
        }

    def detect(self, image: np.ndarray, beacon_gt: tuple[float, float] = None, tolerance_px: float = 5.0) -> dict:
        """
        Executes classical and AI detectors independently, then performs spatial candidate fusion.
        """
        img_arr = np.asarray(image)

        # 1. Classical Detection Branch
        t_c0 = time.perf_counter()
        binary_mask = (img_arr > self.classical_detector.threshold).astype(np.uint8)
        all_features = extract_component_features(img_arr, binary_mask)
        retained_features = self.combined_filter_fn(all_features)
        
        filtered_mask = np.zeros_like(binary_mask, dtype=np.uint8)
        if retained_features:
            num_labels, labels, _, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
            retained_labels = [c["label"] for c in retained_features]
            mask_retained = np.isin(labels, retained_labels)
            filtered_mask[mask_retained] = 1

        class_res = self.classical_detector.detect(img_arr, beacon_gt=beacon_gt, tolerance_px=tolerance_px, binary_mask=filtered_mask)
        t_c1 = time.perf_counter()
        classical_latency_ms = (t_c1 - t_c0) * 1000.0

        # 2. AI Detection Branch
        t_a0 = time.perf_counter()
        ai_res = self.ai_detector.detect(img_arr, beacon_gt=beacon_gt, tolerance_px=tolerance_px)
        t_a1 = time.perf_counter()
        ai_latency_ms = (t_a1 - t_a0) * 1000.0

        # 3. Spatial Candidate Fusion
        t_f0 = time.perf_counter()
        fused = self.fuse_results(class_res, ai_res, frame=img_arr)
        t_f1 = time.perf_counter()
        fusion_latency_ms = (t_f1 - t_f0) * 1000.0
        total_latency_ms = classical_latency_ms + ai_latency_ms + fusion_latency_ms

        fused["classical_latency_ms"] = classical_latency_ms
        fused["ai_latency_ms"] = ai_latency_ms
        fused["fusion_latency_ms"] = fusion_latency_ms
        fused["total_latency_ms"] = total_latency_ms
        fused["classical_res"] = class_res
        fused["ai_res"] = ai_res
        return fused
