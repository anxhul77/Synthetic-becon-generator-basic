import numpy as np
from .localization_base import LocalizationAlgorithm, LocalizationResult
from .background_estimator import estimate_border_background

class BoundingBoxCenterLocalization(LocalizationAlgorithm):
    """
    Algorithm 1: Bounding-box center.
    Establishes a simple geometric localization baseline by thresholding the ROI
    and calculating the geometric center of the foreground bounding box.
    """
    def __init__(self, threshold_offset: float = 15.0, use_sigma_multiplier: bool = True, sigma_k: float = 3.0):
        super().__init__(name="Bounding Box Center")
        self.threshold_offset = float(threshold_offset)
        self.use_sigma_multiplier = bool(use_sigma_multiplier)
        self.sigma_k = float(sigma_k)

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        bg_mean, bg_std = estimate_border_background(roi_image)

        if self.use_sigma_multiplier and bg_std > 1e-6:
            threshold = bg_mean + max(self.threshold_offset, self.sigma_k * bg_std)
        else:
            threshold = bg_mean + self.threshold_offset

        fg_mask = (roi_image > threshold)
        y_indices, x_indices = np.nonzero(fg_mask)

        if len(x_indices) == 0:
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason="No foreground pixels thresholded",
                fit_parameters={
                    "background_mean": bg_mean,
                    "background_std": bg_std,
                    "threshold": threshold,
                    "num_fg_pixels": 0
                }
            )

        xmin_fg, xmax_fg = int(np.min(x_indices)), int(np.max(x_indices))
        ymin_fg, ymax_fg = int(np.min(y_indices)), int(np.max(y_indices))

        bb_width = xmax_fg - xmin_fg + 1
        bb_height = ymax_fg - ymin_fg + 1
        bb_area = bb_width * bb_height

        x_roi = (xmin_fg + xmax_fg) / 2.0
        y_roi = (ymin_fg + ymax_fg) / 2.0

        return LocalizationResult(
            method_name=self.name,
            success=True,
            x_roi=float(x_roi),
            y_roi=float(y_roi),
            fit_parameters={
                "background_mean": bg_mean,
                "background_std": bg_std,
                "threshold": threshold,
                "num_fg_pixels": int(len(x_indices)),
                "bb_xmin": xmin_fg,
                "bb_xmax": xmax_fg,
                "bb_ymin": ymin_fg,
                "bb_ymax": ymax_fg,
                "bb_width": bb_width,
                "bb_height": bb_height,
                "bb_area": bb_area
            }
        )
