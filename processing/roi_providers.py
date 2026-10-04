"""
ROI Provider Architecture for FSOC Beacon Tracking & Localization.

Provides ROI extraction strategies to clearly separate:
1. Estimator-only benchmark: Ground-truth ROI (clearly labeled as 'Estimator-Only (Ground-Truth ROI)').
2. End-to-end benchmark: Detector-derived ROI, Previous Track State ROI, Predicted State ROI, or Reacquisition Search ROI.
"""

from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
import numpy as np

from experiments.exp07_localization.src.roi_extractor import ROICrop, ROIExtractor
from processing.detector import ClassicalBeaconDetector
from processing.adaptive_pipeline import ReframedBeaconDetector


@dataclass
class ExtendedROICrop(ROICrop):
    roi_source_type: str = "estimator_only_gt" # 'estimator_only_gt', 'end_to_end_detector', 'end_to_end_previous_track', 'end_to_end_predicted_track', 'end_to_end_reacquisition'
    provider_label: str = "Estimator-Only (Ground-Truth ROI)"
    detection_successful: bool = True
    detection_confidence: float = 1.0


class BaseROIProvider:
    """Abstract base class for ROI Providers."""
    def __init__(self, roi_size: int = 31, name: str = "Base ROI Provider"):
        self.roi_size = int(roi_size)
        self.name = name
        self.extractor = ROIExtractor(roi_size=roi_size)

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        raise NotImplementedError


class GroundTruthROIProvider(BaseROIProvider):
    """
    Estimator-Only Benchmark Provider:
    Crops ROI centered on ground-truth beacon position (x_true, y_true).
    Explicitly labeled as Estimator-Only.
    """
    def __init__(self, roi_size: int = 31):
        super().__init__(roi_size=roi_size, name="Estimator-Only (Ground-Truth ROI)")

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        base_crop = self.extractor.extract_roi(image, x_true, y_true)
        return ExtendedROICrop(
            roi_image=base_crop.roi_image,
            xmin=base_crop.xmin,
            ymin=base_crop.ymin,
            xmax=base_crop.xmax,
            ymax=base_crop.ymax,
            width=base_crop.width,
            height=base_crop.height,
            x_true_full=base_crop.x_true_full,
            y_true_full=base_crop.y_true_full,
            x_true_roi=base_crop.x_true_roi,
            y_true_roi=base_crop.y_true_roi,
            roi_center_x=base_crop.roi_center_x,
            roi_center_y=base_crop.roi_center_y,
            crop_offset_x=base_crop.crop_offset_x,
            crop_offset_y=base_crop.crop_offset_y,
            is_out_of_bounds=base_crop.is_out_of_bounds,
            roi_source_type="estimator_only_gt",
            provider_label="Estimator-Only (Ground-Truth ROI)",
            detection_successful=True,
            detection_confidence=1.0
        )


class DetectorROIProvider(BaseROIProvider):
    """
    End-to-End Benchmark Provider (Detector-Derived ROI):
    Runs optical beacon detector (Classical or Reframed CFAR) on full frame to obtain candidate ROI center.
    """
    def __init__(self, roi_size: int = 31, detector_type: str = "reframed", threshold: float = 160.0):
        super().__init__(roi_size=roi_size, name="End-to-End (Detector ROI)")
        self.detector_type = detector_type.lower()
        if self.detector_type == "classical":
            self.detector = ClassicalBeaconDetector(threshold=threshold)
        else:
            self.detector = ReframedBeaconDetector()

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        det = detector_override if detector_override is not None else self.detector
        det_res = det.detect(image, beacon_gt=(x_true, y_true))

        if det_res.get("detected", False) and det_res.get("x_est") is not None:
            cx_det = det_res["x_est"]
            cy_det = det_res["y_est"]
            conf = det_res.get("confidence", 1.0)
            det_success = True
        else:
            # Fallback to image center if detector finds no candidates (detection failure)
            h, w = image.shape[:2]
            cx_det, cy_det = w / 2.0, h / 2.0
            conf = 0.0
            det_success = False

        base_crop = self.extractor.extract_roi(image, cx_det, cy_det)
        
        # Calculate ground truth relative to ROI
        x_true_roi = x_true - base_crop.xmin
        y_true_roi = y_true - base_crop.ymin
        roi_center_x = base_crop.width / 2.0
        roi_center_y = base_crop.height / 2.0
        crop_offset_x = x_true_roi - roi_center_x
        crop_offset_y = y_true_roi - roi_center_y

        return ExtendedROICrop(
            roi_image=base_crop.roi_image,
            xmin=base_crop.xmin,
            ymin=base_crop.ymin,
            xmax=base_crop.xmax,
            ymax=base_crop.ymax,
            width=base_crop.width,
            height=base_crop.height,
            x_true_full=float(x_true),
            y_true_full=float(y_true),
            x_true_roi=float(x_true_roi),
            y_true_roi=float(y_true_roi),
            roi_center_x=float(roi_center_x),
            roi_center_y=float(roi_center_y),
            crop_offset_x=float(crop_offset_x),
            crop_offset_y=float(crop_offset_y),
            is_out_of_bounds=base_crop.is_out_of_bounds,
            roi_source_type="end_to_end_detector",
            provider_label="End-to-End (Detector ROI)",
            detection_successful=det_success,
            detection_confidence=conf
        )


class PreviousTrackStateROIProvider(BaseROIProvider):
    """
    End-to-End Benchmark Provider (Previous Track State ROI):
    Obtains ROI centered on the estimated state (x_hat_{t-1}, y_hat_{t-1}) from the previous frame.
    """
    def __init__(self, roi_size: int = 31):
        super().__init__(roi_size=roi_size, name="End-to-End (Previous Track State ROI)")

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        if previous_track_state is not None:
            cx, cy = previous_track_state
            track_valid = True
        else:
            cx, cy = x_true, y_true  # Initialization fallback
            track_valid = False

        base_crop = self.extractor.extract_roi(image, cx, cy)

        x_true_roi = x_true - base_crop.xmin
        y_true_roi = y_true - base_crop.ymin
        roi_center_x = base_crop.width / 2.0
        roi_center_y = base_crop.height / 2.0
        crop_offset_x = x_true_roi - roi_center_x
        crop_offset_y = y_true_roi - roi_center_y

        return ExtendedROICrop(
            roi_image=base_crop.roi_image,
            xmin=base_crop.xmin,
            ymin=base_crop.ymin,
            xmax=base_crop.xmax,
            ymax=base_crop.ymax,
            width=base_crop.width,
            height=base_crop.height,
            x_true_full=float(x_true),
            y_true_full=float(y_true),
            x_true_roi=float(x_true_roi),
            y_true_roi=float(y_true_roi),
            roi_center_x=float(roi_center_x),
            roi_center_y=float(roi_center_y),
            crop_offset_x=float(crop_offset_x),
            crop_offset_y=float(crop_offset_y),
            is_out_of_bounds=base_crop.is_out_of_bounds,
            roi_source_type="end_to_end_previous_track",
            provider_label="End-to-End (Previous Track State ROI)",
            detection_successful=track_valid,
            detection_confidence=1.0 if track_valid else 0.5
        )


class PredictedStateROIProvider(BaseROIProvider):
    """
    End-to-End Benchmark Provider (Predicted State ROI):
    Obtains ROI centered on Kalman Filter motion prediction (x_bar_t, y_bar_t).
    """
    def __init__(self, roi_size: int = 31):
        super().__init__(roi_size=roi_size, name="End-to-End (Predicted State ROI)")

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        if predicted_track_state is not None:
            cx, cy = predicted_track_state
            pred_valid = True
        else:
            cx, cy = x_true, y_true
            pred_valid = False

        base_crop = self.extractor.extract_roi(image, cx, cy)

        x_true_roi = x_true - base_crop.xmin
        y_true_roi = y_true - base_crop.ymin
        roi_center_x = base_crop.width / 2.0
        roi_center_y = base_crop.height / 2.0
        crop_offset_x = x_true_roi - roi_center_x
        crop_offset_y = y_true_roi - roi_center_y

        return ExtendedROICrop(
            roi_image=base_crop.roi_image,
            xmin=base_crop.xmin,
            ymin=base_crop.ymin,
            xmax=base_crop.xmax,
            ymax=base_crop.ymax,
            width=base_crop.width,
            height=base_crop.height,
            x_true_full=float(x_true),
            y_true_full=float(y_true),
            x_true_roi=float(x_true_roi),
            y_true_roi=float(y_true_roi),
            roi_center_x=float(roi_center_x),
            roi_center_y=float(roi_center_y),
            crop_offset_x=float(crop_offset_x),
            crop_offset_y=float(crop_offset_y),
            is_out_of_bounds=base_crop.is_out_of_bounds,
            roi_source_type="end_to_end_predicted_track",
            provider_label="End-to-End (Predicted State ROI)",
            detection_successful=pred_valid,
            detection_confidence=1.0 if pred_valid else 0.5
        )


class ReacquisitionSearchROIProvider(BaseROIProvider):
    """
    End-to-End Benchmark Provider (Reacquisition Search ROI):
    Executes a search pattern (grid/expanding ROI) over spatial uncertainty region when track is lost.
    """
    def __init__(self, roi_size: int = 31, search_grid_size: int = 3):
        super().__init__(roi_size=roi_size, name="End-to-End (Reacquisition Search ROI)")
        self.search_grid_size = search_grid_size

    def get_roi(
        self,
        image: np.ndarray,
        x_true: float,
        y_true: float,
        previous_track_state: Optional[Tuple[float, float]] = None,
        predicted_track_state: Optional[Tuple[float, float]] = None,
        detector_override: Optional[Any] = None
    ) -> ExtendedROICrop:
        center_x = predicted_track_state[0] if predicted_track_state else x_true
        center_y = predicted_track_state[1] if predicted_track_state else y_true

        # Perform peak search in expanded search region around predicted state
        h, w = image.shape[:2]
        win_size = self.roi_size * 2
        xmin_search = int(max(0, center_x - win_size // 2))
        ymin_search = int(max(0, center_y - win_size // 2))
        xmax_search = int(min(w, center_x + win_size // 2))
        ymax_search = int(min(h, center_y + win_size // 2))

        search_sub = image[ymin_search:ymax_search, xmin_search:xmax_search]
        if search_sub.size > 0:
            max_idx = np.unravel_index(np.argmax(search_sub), search_sub.shape)
            found_y = ymin_search + max_idx[0]
            found_x = xmin_search + max_idx[1]
        else:
            found_x, found_y = center_x, center_y

        base_crop = self.extractor.extract_roi(image, found_x, found_y)

        x_true_roi = x_true - base_crop.xmin
        y_true_roi = y_true - base_crop.ymin
        roi_center_x = base_crop.width / 2.0
        roi_center_y = base_crop.height / 2.0
        crop_offset_x = x_true_roi - roi_center_x
        crop_offset_y = y_true_roi - roi_center_y

        return ExtendedROICrop(
            roi_image=base_crop.roi_image,
            xmin=base_crop.xmin,
            ymin=base_crop.ymin,
            xmax=base_crop.xmax,
            ymax=base_crop.ymax,
            width=base_crop.width,
            height=base_crop.height,
            x_true_full=float(x_true),
            y_true_full=float(y_true),
            x_true_roi=float(x_true_roi),
            y_true_roi=float(y_true_roi),
            roi_center_x=float(roi_center_x),
            roi_center_y=float(roi_center_y),
            crop_offset_x=float(crop_offset_x),
            crop_offset_y=float(crop_offset_y),
            is_out_of_bounds=base_crop.is_out_of_bounds,
            roi_source_type="end_to_end_reacquisition",
            provider_label="End-to-End (Reacquisition Search ROI)",
            detection_successful=True,
            detection_confidence=0.8
        )
