import numpy as np
from .localization_base import LocalizationAlgorithm, LocalizationResult
from .background_estimator import estimate_border_background

class BinaryCentroidLocalization(LocalizationAlgorithm):
    """
    Algorithm 2: Binary centroid.
    Evaluates localization using the arithmetic mean (centroid) of thresholded foreground pixels.
    """
    def __init__(self, threshold_offset: float = 15.0, use_sigma_multiplier: bool = True, sigma_k: float = 3.0):
        super().__init__(name="Binary Centroid")
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

        N = len(x_indices)
        if N == 0:
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

        x_roi = float(np.mean(x_indices))
        y_roi = float(np.mean(y_indices))

        return LocalizationResult(
            method_name=self.name,
            success=True,
            x_roi=x_roi,
            y_roi=y_roi,
            fit_parameters={
                "background_mean": bg_mean,
                "background_std": bg_std,
                "threshold": threshold,
                "num_fg_pixels": int(N)
            }
        )
