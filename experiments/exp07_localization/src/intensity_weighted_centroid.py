import numpy as np
from .localization_base import LocalizationAlgorithm, LocalizationResult
from .background_estimator import estimate_border_background, estimate_gradient_background

class IntensityWeightedCentroidLocalization(LocalizationAlgorithm):
    """
    Algorithm 3: Intensity-weighted centroid.
    Estimates the beacon center using background-corrected, nonnegative pixel intensity weights:
    w_i = max(I_i - B_i, 0)
    x_c = sum(w_i * x_i) / sum(w_i)
    y_c = sum(w_i * y_i) / sum(w_i)
    """
    def __init__(self, bg_model_type: str = "border"):
        super().__init__(name="Intensity-Weighted Centroid")
        self.bg_model_type = bg_model_type

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        h, w = roi_image.shape
        x_coords = np.arange(w, dtype=np.float64)
        y_coords = np.arange(h, dtype=np.float64)
        xx, yy = np.meshgrid(x_coords, y_coords)

        if self.bg_model_type == "gradient":
            B0, a, b = estimate_gradient_background(roi_image)
            bg_map = B0 + a * xx + b * yy
            bg_mean = B0
        else:
            bg_mean, _ = estimate_border_background(roi_image)
            bg_map = np.full((h, w), bg_mean, dtype=np.float64)

        weights = np.maximum(0.0, roi_image - bg_map)
        total_weight = float(np.sum(weights))

        if not np.isfinite(total_weight) or total_weight <= 0.0:
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason="Total effective weight is zero or nonfinite",
                fit_parameters={
                    "background_mean": bg_mean,
                    "total_weight": 0.0,
                    "max_weight": float(np.max(weights)) if len(weights) > 0 else 0.0
                }
            )

        x_roi = float(np.sum(xx * weights) / total_weight)
        y_roi = float(np.sum(yy * weights) / total_weight)

        return LocalizationResult(
            method_name=self.name,
            success=True,
            x_roi=x_roi,
            y_roi=y_roi,
            fit_parameters={
                "background_mean": bg_mean,
                "total_weight": total_weight,
                "max_weight": float(np.max(weights))
            }
        )
