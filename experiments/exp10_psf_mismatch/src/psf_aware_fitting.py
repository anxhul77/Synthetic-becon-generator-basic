import numpy as np
from scipy.optimize import curve_fit
from typing import Dict, Any, Optional

from experiments.exp07_localization.src.localization_base import LocalizationAlgorithm, LocalizationResult
from experiments.exp07_localization.src.background_estimator import estimate_border_background
from generator.psf import get_psf_model, PSFModel


class PSFAwareFittingLocalization(LocalizationAlgorithm):
    """
    PSF-Aware Fitter for Experiment 10:
    Estimates the beacon center (x0, y0), peak amplitude A, and background B by fitting
    the camera's calibrated PSF model family (Gaussian, Elliptical, Asymmetric, Defocused, or Aberrated).
    Must be initialized from ROI-derived statistics, NEVER ground-truth coordinates.
    """
    def __init__(self, psf_family: str = "gaussian", maxfev: int = 1000, **psf_kwargs):
        name = f"PSF-Aware Fitting ({psf_family.replace('_', ' ').title()})"
        super().__init__(name=name)
        self.psf_family = str(psf_family).lower()
        self.maxfev = int(maxfev)
        self.psf_kwargs = psf_kwargs

    def _localize_roi(self, roi_image: np.ndarray, **kwargs) -> LocalizationResult:
        h, w = roi_image.shape
        x_coords = np.arange(w, dtype=np.float64)
        y_coords = np.arange(h, dtype=np.float64)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Merge init kwargs with call kwargs
        merged_kwargs = {**self.psf_kwargs, **kwargs}
        psf_family = str(kwargs.get("psf_family", self.psf_family)).lower()

        bg_init, bg_std = estimate_border_background(roi_image)
        max_val = float(np.max(roi_image))
        amp_init = max(1.0, max_val - bg_init)

        # ROI-derived initial position: geometric center of ROI
        x0_init = w / 2.0
        y0_init = h / 2.0

        def model_func(coords, A, x0, y0, B):
            psf_model = get_psf_model(psf_type=psf_family, **merged_kwargs)
            rendered_signal = psf_model.render(coords[0], coords[1], x0, y0, A)
            return (B + rendered_signal).ravel()

        p0 = [amp_init, x0_init, y0_init, bg_init]
        bounds = (
            [0.0, -5.0, -5.0, 0.0],
            [1000.0, w + 5.0, h + 5.0, 1000.0]
        )

        try:
            popt, pcov = curve_fit(
                model_func,
                (xx, yy),
                roi_image.ravel(),
                p0=p0,
                bounds=bounds,
                maxfev=self.maxfev
            )

            fit_A, fit_x0, fit_y0, fit_B = popt

            fitted_vals = model_func((xx, yy), *popt).reshape(h, w)
            residual = roi_image - fitted_vals
            residual_rmse = float(np.sqrt(np.mean(residual ** 2)))

            if not np.all(np.isfinite(popt)):
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason="Non-finite parameters returned by PSF-aware optimizer",
                    fit_parameters={"initial_params": p0}
                )

            if fit_x0 < -2.0 or fit_x0 > w + 2.0 or fit_y0 < -2.0 or fit_y0 > h + 2.0:
                return LocalizationResult(
                    method_name=self.name,
                    success=False,
                    failure_reason="Fitted center shifted beyond acceptable ROI boundary",
                    fit_parameters={"fitted_x0": float(fit_x0), "fitted_y0": float(fit_y0)}
                )

            return LocalizationResult(
                method_name=self.name,
                success=True,
                x_roi=float(fit_x0),
                y_roi=float(fit_y0),
                fit_parameters={
                    "fitted_amplitude": float(fit_A),
                    "fitted_bg": float(fit_B),
                    "residual_rmse": residual_rmse,
                    "psf_family": psf_family
                }
            )

        except Exception as e:
            return LocalizationResult(
                method_name=self.name,
                success=False,
                failure_reason=f"PSF-aware curve fit non-convergence: {str(e)}",
                fit_parameters={"initial_params": p0}
            )
