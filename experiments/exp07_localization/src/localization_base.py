import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
from .roi_extractor import ROICrop, roi_to_full_coords

@dataclass
class LocalizationResult:
    method_name: str
    success: bool
    x_est: Optional[float] = None
    y_est: Optional[float] = None
    x_roi: Optional[float] = None
    y_roi: Optional[float] = None
    failure_reason: Optional[str] = None
    runtime_ms: float = 0.0
    fit_parameters: Dict[str, Any] = field(default_factory=dict)
    diagnostic_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "success": self.success,
            "x_est": self.x_est,
            "y_est": self.y_est,
            "x_roi": self.x_roi,
            "y_roi": self.y_roi,
            "failure_reason": self.failure_reason,
            "runtime_ms": self.runtime_ms,
            "fit_parameters": self.fit_parameters,
            "diagnostic_info": self.diagnostic_info
        }

class LocalizationAlgorithm:
    """
    Common Abstract Base Interface for all beacon localization algorithms.
    Each algorithm accepts an ROI crop and estimates the subpixel position of the beacon.
    MUST NOT use ground-truth subpixel position as an input or initialization.
    """
    def __init__(self, name: str):
        self.name = name

    def localize(self, roi_crop: ROICrop, **kwargs) -> LocalizationResult:
        t0 = time.perf_counter()
        try:
            res = self._localize_roi(roi_crop.roi_image, **kwargs)
            t1 = time.perf_counter()
            res.runtime_ms = (t1 - t0) * 1000.0

            if res.success and res.x_roi is not None and res.y_roi is not None:
                res.x_est, res.y_est = roi_to_full_coords(res.x_roi, res.y_roi, roi_crop.xmin, roi_crop.ymin)
            else:
                res.x_est = None
                res.y_est = None
            return res
        except Exception as e:
            t1 = time.perf_counter()
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason=f"Exception: {str(e)}",
                runtime_ms=(t1 - t0) * 1000.0
            )

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        raise NotImplementedError
