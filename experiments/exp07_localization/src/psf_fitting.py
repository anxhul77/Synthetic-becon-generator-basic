import numpy as np
from scipy.optimize import curve_fit
from .localization_base import LocalizationAlgorithm, LocalizationResult
from .background_estimator import estimate_border_background

def known_psf_model(coords: tuple[np.ndarray, np.ndarray], A: float, x0: float, y0: float, B: float, sigma_x: float, sigma_y: float) -> np.ndarray:
    xx, yy = coords
    term_x = ((xx - x0) ** 2) / (2.0 * sigma_x ** 2)
    term_y = ((yy - y0) ** 2) / (2.0 * sigma_y ** 2)
    return (B + A * np.exp(-(term_x + term_y))).ravel()

class PSFFittingLocalization(LocalizationAlgorithm):
    """
    Algorithm 5: PSF fitting (Calibrated/Known PSF model).
    Estimates the beacon location by fitting the camera's known, calibrated Point Spread Function (PSF).
    In the primary configuration, the PSF shape parameters (sigma_x, sigma_y) are FIXED to their
    calibrated nominal values, while amplitude (A), background (B), and center (x0, y0) are estimated.
    Supports an optional mode where width estimation is enabled for model mismatch analysis.
    """
    def __init__(self, calibrated_sigma_x: float = 2.0, calibrated_sigma_y: float = 2.0, estimate_width: bool = False, maxfev: int = 1000):
        name = "PSF Fitting (Known PSF)" if not estimate_width else "PSF Fitting (Estimated Width)"
        super().__init__(name=name)
        self.calibrated_sigma_x = float(calibrated_sigma_x)
        self.calibrated_sigma_y = float(calibrated_sigma_y)
        self.estimate_width = bool(estimate_width)
        self.maxfev = int(maxfev)

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        h, w = roi_image.shape
        x_coords = np.arange(w, dtype=np.float64)
        y_coords = np.arange(h, dtype=np.float64)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Allow passing override PSF shape from kwargs if evaluating model mismatch
        sig_x = float(kwargs.get("calibrated_sigma_x", self.calibrated_sigma_x))
        sig_y = float(kwargs.get("calibrated_sigma_y", self.calibrated_sigma_y))

        bg_init, bg_std = estimate_border_background(roi_image)
        max_val = float(np.max(roi_image))
        amp_init = max(1.0, max_val - bg_init)

        x0_init = w / 2.0
        y0_init = h / 2.0

        if not self.estimate_width:
            # Model function wrapper fixing sigma_x and sigma_y
            def psf_func(coords, A, x0, y0, B):
                return known_psf_model(coords, A, x0, y0, B, sig_x, sig_y)

            p0 = [amp_init, x0_init, y0_init, bg_init]
            bounds = (
                [0.0, -5.0, -5.0, 0.0],
                [1000.0, w + 5.0, h + 5.0, 1000.0]
            )

            try:
                popt, pcov = curve_fit(
                    psf_func,
                    (xx, yy),
                    roi_image.ravel(),
                    p0=p0,
                    bounds=bounds,
                    maxfev=self.maxfev
                )
                fit_A, fit_x0, fit_y0, fit_B = popt
                fit_sig_x, fit_sig_y = sig_x, sig_y
            except Exception as e:
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason=f"PSF fit non-convergence: {str(e)}",
                    fit_parameters={"calibrated_sigma_x": sig_x, "calibrated_sigma_y": sig_y}
                )
        else:
            p0 = [amp_init, x0_init, y0_init, sig_x, sig_y, bg_init]
            bounds = (
                [0.0, -5.0, -5.0, 0.1, 0.1, 0.0],
                [1000.0, w + 5.0, h + 5.0, float(w), float(h), 1000.0]
            )

            try:
                def psf_func_est(coords, A, x0, y0, sx, sy, B):
                    return known_psf_model(coords, A, x0, y0, B, sx, sy)

                popt, pcov = curve_fit(
                    psf_func_est,
                    (xx, yy),
                    roi_image.ravel(),
                    p0=p0,
                    bounds=bounds,
                    maxfev=self.maxfev
                )
                fit_A, fit_x0, fit_y0, fit_sig_x, fit_sig_y, fit_B = popt
            except Exception as e:
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason=f"PSF fit non-convergence: {str(e)}",
                    fit_parameters={"initial_params": p0}
                )

        # Residual calculation
        fitted_vals = known_psf_model((xx, yy), fit_A, fit_x0, fit_y0, fit_B, fit_sig_x, fit_sig_y).reshape(h, w)
        residual = roi_image - fitted_vals
        residual_rmse = float(np.sqrt(np.mean(residual ** 2)))

        if not np.all(np.isfinite(popt)):
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason="Non-finite parameters returned by PSF curve_fit",
                fit_parameters={"calibrated_sigma_x": sig_x, "calibrated_sigma_y": sig_y}
            )

        if fit_x0 < -2.0 or fit_x0 > w + 2.0 or fit_y0 < -2.0 or fit_y0 > h + 2.0:
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason="Fitted center shifted beyond ROI boundary",
                fit_parameters={
                    "fitted_x0": float(fit_x0),
                    "fitted_y0": float(fit_y0),
                    "fitted_amplitude": float(fit_A),
                    "fitted_bg": float(fit_B)
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
                "calibrated_sigma_x": fit_sig_x,
                "calibrated_sigma_y": fit_sig_y,
                "residual_rmse": residual_rmse,
                "estimate_width": self.estimate_width
            }
        )
