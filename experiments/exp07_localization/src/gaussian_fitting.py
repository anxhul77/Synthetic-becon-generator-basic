import numpy as np
from scipy.optimize import curve_fit
from .localization_base import LocalizationAlgorithm, LocalizationResult
from .background_estimator import estimate_border_background

def gaussian_2d_model(coords: tuple[np.ndarray, np.ndarray], A: float, x0: float, y0: float, sigma_x: float, sigma_y: float, B: float) -> np.ndarray:
    xx, yy = coords
    term_x = ((xx - x0) ** 2) / (2.0 * sigma_x ** 2)
    term_y = ((yy - y0) ** 2) / (2.0 * sigma_y ** 2)
    return (B + A * np.exp(-(term_x + term_y))).ravel()

class GaussianFittingLocalization(LocalizationAlgorithm):
    """
    Algorithm 4: 2D Gaussian fitting.
    Fits a 2D Gaussian intensity model to the ROI, estimating amplitude, center, widths (sigma_x, sigma_y),
    and background level using nonlinear least squares optimization.
    Must be initialized from ROI-derived statistics, NEVER ground-truth coordinates.
    """
    def __init__(self, maxfev: int = 1000):
        super().__init__(name="Gaussian Fitting")
        self.maxfev = int(maxfev)

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        h, w = roi_image.shape
        x_coords = np.arange(w, dtype=np.float64)
        y_coords = np.arange(h, dtype=np.float64)
        xx, yy = np.meshgrid(x_coords, y_coords)

        bg_init, bg_std = estimate_border_background(roi_image)
        max_val = float(np.max(roi_image))
        amp_init = max(1.0, max_val - bg_init)

        # ROI-derived initial position: geometric center of ROI
        x0_init = w / 2.0
        y0_init = h / 2.0
        sigma_init = 2.0

        p0 = [amp_init, x0_init, y0_init, sigma_init, sigma_init, bg_init]
        bounds = (
            [0.0, -5.0, -5.0, 0.1, 0.1, 0.0],
            [1000.0, w + 5.0, h + 5.0, float(w), float(h), 1000.0]
        )

        nfev = 0
        try:
            popt, pcov = curve_fit(
                gaussian_2d_model,
                (xx, yy),
                roi_image.ravel(),
                p0=p0,
                bounds=bounds,
                maxfev=self.maxfev
            )

            fit_A, fit_x0, fit_y0, fit_sigma_x, fit_sigma_y, fit_B = popt

            # Calculate residual norm
            fitted_vals = gaussian_2d_model((xx, yy), *popt).reshape(h, w)
            residual = roi_image - fitted_vals
            residual_ss = float(np.sum(residual ** 2))
            residual_rmse = float(np.sqrt(np.mean(residual ** 2)))

            # Validate parameters
            if not np.all(np.isfinite(popt)):
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason="Non-finite parameters returned by curve_fit",
                    fit_parameters={"initial_params": p0}
                )

            if fit_x0 < -2.0 or fit_x0 > w + 2.0 or fit_y0 < -2.0 or fit_y0 > h + 2.0:
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason="Fitted center shifted beyond acceptable ROI boundary",
                    fit_parameters={
                        "fitted_x0": float(fit_x0),
                        "fitted_y0": float(fit_y0),
                        "fitted_amplitude": float(fit_A),
                        "fitted_bg": float(fit_B),
                        "fitted_sigma_x": float(fit_sigma_x),
                        "fitted_sigma_y": float(fit_sigma_y)
                    }
                )

            return LocalizationResult(
                method_name=self.name,
                success=True,
                x_roi=float(fit_x0),
                y_roi=float(fit_y0),
                fit_parameters={
                    "fitted_amplitude": float(fit_A),
                    "fitted_bg": float(fit_B),
                    "fitted_sigma_x": float(fit_sigma_x),
                    "fitted_sigma_y": float(fit_sigma_y),
                    "residual_rmse": residual_rmse,
                    "residual_ss": residual_ss
                },
                diagnostic_info={
                    "pcov_trace": float(np.trace(pcov)) if pcov is not None and np.all(np.isfinite(pcov)) else None
                }
            )

        except Exception as e:
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason=f"Curve fit non-convergence / optimizer error: {str(e)}",
                fit_parameters={"initial_params": p0}
            )
