import time
import numpy as np
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

from processing.detector import ClassicalBeaconDetector
from processing.component_filtering import get_component_filter
from experiments.exp06_classical_vs_ai.ai_detector import AIBeaconDetector
from experiments.exp06_classical_vs_ai.hybrid_detector import HybridBeaconDetector

class ParallelBeaconPipeline:
    """
    Architecture B — Parallel Pipeline for FSOC Beacon Processing:
    Input Frame -> Concurrent Submissions [ Classical Detector || AI Detector ] -> Sync -> Fusion -> Localization -> Result
    """
    def __init__(self,
                 classical_threshold: float = 160.0,
                 model_path: str = "results/exp06_classical_vs_ai/models/exp06_beacon_ai_model.pt",
                 confidence_threshold: float = 0.5,
                 matching_radius_px: float = 5.0,
                 max_workers: int = 2):

        self.classical_detector = ClassicalBeaconDetector(threshold=classical_threshold, min_area=3)
        self.ai_detector = AIBeaconDetector(model_path=model_path, confidence_threshold=confidence_threshold)
        self.hybrid_detector = HybridBeaconDetector(
            classical_detector=self.classical_detector,
            ai_detector=self.ai_detector,
            matching_radius_px=matching_radius_px
        )

        self.combined_filter_fn, _ = get_component_filter("combined", {
            "min_area": 3, "max_area": 50, "max_aspect_ratio": 2.0,
            "min_circularity": 0.5, "min_peak_intensity": 180.0
        })
        self.threshold = classical_threshold
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="FSOC_Pipeline")

    def _run_classical(self, frame: np.ndarray, beacon_gt: tuple[float, float]) -> tuple[dict, float]:
        t0 = time.perf_counter()
        c_res = self.classical_detector.detect(frame, beacon_gt=beacon_gt)
        t1 = time.perf_counter()
        return c_res, (t1 - t0) * 1000.0

    def _run_ai(self, frame: np.ndarray, beacon_gt: tuple[float, float]) -> tuple[dict, float]:
        t0 = time.perf_counter()
        a_res = self.ai_detector.detect(frame, beacon_gt=beacon_gt)
        t1 = time.perf_counter()
        return a_res, (t1 - t0) * 1000.0

    def process_frame(self, frame: np.ndarray, frame_id: str, beacon_gt: tuple[float, float] = None) -> Dict[str, Any]:
        """
        Submits Classical and AI detection tasks concurrently and synchronizes before fusion.
        """
        t_start = time.perf_counter()

        # Dispatch tasks
        t_disp0 = time.perf_counter()
        future_c = self.executor.submit(self._run_classical, frame, beacon_gt)
        future_a = self.executor.submit(self._run_ai, frame, beacon_gt)
        t_disp1 = time.perf_counter()
        t_dispatch_ms = (t_disp1 - t_disp0) * 1000.0

        # Synchronization stage
        t_sync0 = time.perf_counter()
        c_res, t_classical_ms = future_c.result()
        a_res, t_ai_ms = future_a.result()
        t_sync1 = time.perf_counter()
        t_sync_ms = (t_sync1 - t_sync0) * 1000.0

        # Fusion & Localization Stage
        t_f0 = time.perf_counter()
        fused_res = self.hybrid_detector.fuse_results(c_res, a_res, frame=frame)
        t_f1 = time.perf_counter()
        t_fusion_loc_ms = (t_f1 - t_f0) * 1000.0

        t_end = time.perf_counter()
        t_end_to_end_ms = (t_end - t_start) * 1000.0

        return {
            "frame_id": frame_id,
            "architecture": "parallel",
            "classical_latency_ms": t_classical_ms,
            "ai_latency_ms": t_ai_ms,
            "dispatch_latency_ms": t_dispatch_ms,
            "synchronization_latency_ms": t_sync_ms,
            "fusion_latency_ms": t_fusion_loc_ms * 0.5,
            "localization_latency_ms": t_fusion_loc_ms * 0.5,
            "end_to_end_latency_ms": t_end_to_end_ms,
            "detected": fused_res["detected"],
            "x_est": fused_res["x_est"] if fused_res["detected"] else np.nan,
            "y_est": fused_res["y_est"] if fused_res["detected"] else np.nan,
            "confidence": fused_res.get("confidence", 1.0),
            "num_candidates": fused_res.get("num_candidates", 0),
            "fusion_status": fused_res.get("fusion_status", "none"),
            "c_res": c_res,
            "a_res": a_res
        }

    def shutdown(self):
        self.executor.shutdown(wait=True)
