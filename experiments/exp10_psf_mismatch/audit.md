# Prerequisite & Codebase Audit — Experiment 10: PSF Mismatch and Localization Robustness

**Date**: September 29, 2026  
**Status**: Completed  
**Target Module**: `experiments/exp10_psf_mismatch`  
**Author**: Senior Computer Vision & FSOC Research Team  

---

## 1. Overview and Purpose

Before implementing **Experiment 10: PSF Mismatch and Localization Robustness**, a comprehensive codebase audit was performed across Experiments 7, 8, and 9 to evaluate existing optical models, continuous subpixel rendering, fitting algorithms, failure handling, and statistical evaluation utilities.

The goal of Experiment 10 is to quantify the localization error, systematic subpixel bias, fitting non-convergence, and runtime penalties incurred when a localization estimator assumes an incorrect Point Spread Function (PSF) model compared to the actual image-generation PSF family across five distinct PSF families:
1. **Isotropic Gaussian** (Matched baseline, $\sigma = 2.0$ px)
2. **Elliptical Gaussian** (Shape mismatch, axis ratios $r \in \{1.0, 1.25, 1.5, 2.0\}$, orientations $\theta \in \{0^\circ, 45^\circ\}$)
3. **Asymmetric PSF** (Asymmetric structure mismatch, main component + secondary displaced component with amplitude ratios $\alpha \in \{0.0, 0.1, 0.2, 0.3\}$)
4. **Defocused PSF** (Optical blur mismatch, $\sigma_{\text{eff}}^2 = \sigma_{\text{nominal}}^2 + \sigma_{\text{defocus}}^2$ with $\sigma_{\text{defocus}} \in \{0.0, 0.5, 1.0, 2.0\}$ px)
5. **Aberrated PSF** (Coma and astigmatism optical distortion wavefront aberrations)

---

## 2. Inventory of Existing Codebase Assets

| Module / Asset | Current Status | Reusability & Audit Findings |
| :--- | :--- | :--- |
| `generator/generator.py` | **Extensible** | Supports continuous subpixel rendering, camera intrinsics ($f_x=f_y=2000$ px), SNR injection, background models, and ground-truth metadata. Requires extension to accept custom `psf_model` instances for Asymmetric, Defocused, and Aberrated PSF families. |
| `generator/psf.py` | **Partial** | Provides `GaussianPSF` and `EllipticalGaussianPSF`. Needs extension to add `AsymmetricPSF`, `DefocusedPSF`, and `AberratedPSF` classes inheriting from `PSFModel`. |
| `experiments/exp07_localization/src/` | **Reusable** | Provides `ROIExtractor`, `IntensityWeightedCentroidLocalization`, `GaussianFittingLocalization`, `PSFFittingLocalization`, and statistical utilities (`compute_pixel_and_angular_errors`, `compute_group_summary_stats`, `compute_paired_comparison`). |
| `experiments/exp08_subpixel_localization/src/` | **Reusable** | Provides `generate_controlled_phase_grid` ($64$ subpixel phase grid points) and phase analysis heatmap tools (`compute_phase_grid_analysis`). |
| `experiments/exp09_psf_width/src/` | **Reusable** | Provides continuous PSF width validation, bootstrap CI computation, and plot generation workflows. |

---

## 3. Mandatory Audit Checklist & Verification

| Audit Check | Status | Verification Result |
| :--- | :--- | :--- |
| **1. Isotropic Gaussian Model** | **VERIFIED** | `GaussianPSF` implements continuous 2D isotropic Gaussian rendering ($I(x,y) = A \exp(-[(x-x_0)^2 + (y-y_0)^2]/(2\sigma^2))$). |
| **2. Elliptical Gaussian Model** | **VERIFIED** | `EllipticalGaussianPSF` implements rotated anisotropic 2D Gaussian rendering with configurable $\sigma_x$, $\sigma_y$, and orientation angle $\theta$. |
| **3. Asymmetric PSF Model** | **MISSING -> ADD** | Needs `AsymmetricPSF` implementation combining a primary optical Gaussian component with a secondary displaced Gaussian component ($A_2 / A_1 \in \{0.0, 0.1, 0.2, 0.3\}$). |
| **4. Defocused PSF Model** | **MISSING -> ADD** | Needs `DefocusedPSF` implementing Gaussian-equivalent defocus expansion ($\sigma_{\text{eff}} = \sqrt{\sigma_{\text{nominal}}^2 + \sigma_{\text{defocus}}^2}$). |
| **5. Aberrated PSF Model** | **MISSING -> ADD** | Needs `AberratedPSF` implementing coma and astigmatism wavefront distortion models. |
| **6. PSF-Aware Fitting Support** | **MISSING -> ADD** | `PSFFittingLocalization` currently fits Gaussian models. Needs extension to support general `psf_model` matching for Elliptical, Asymmetric, Defocused, and Aberrated PSF families. |
| **7. Gaussian Fitting Fitter Baseline** | **VERIFIED** | `GaussianFittingLocalization` fits a 6-parameter isotropic/anisotropic Gaussian model ($A, x_0, y_0, \sigma_x, \sigma_y, B$) without receiving ground-truth coordinates. |
| **8. Zero Ground-Truth Leakage** | **VERIFIED** | Fitter algorithms use image-derived initial estimates (geometric ROI center and border background mean). Ground-truth coordinates are never passed to estimators. |

---

## 4. Required Codebase Modifications & Strategy

1. **Extend `generator/psf.py`**:
   - Implement `AsymmetricPSF` (main component at $(x_0, y_0)$ + secondary component at $(x_0 + \Delta x, y_0 + \Delta y)$ with relative amplitude $\alpha$).
   - Implement `DefocusedPSF` ($\sigma_{\text{eff}} = \sqrt{\sigma_0^2 + \sigma_{\text{defocus}}^2}$).
   - Implement `AberratedPSF` (coma / astigmatism optical distortion model).
   - Implement `PSFFactory` for unified model instantiation from configuration.

2. **Extend `SyntheticBeaconGenerator` in `generator/generator.py`**:
   - Update `generate_frame` to accept arbitrary `psf_model` objects or `psf_type` identifiers.

3. **Create `experiments/exp10_psf_mismatch/src/psf_aware_fitting.py`**:
   - Implement `PSFAwareFittingLocalization` capable of fitting the exact actual PSF model family when configured (calibrated matched model) or fitting an isotropic Gaussian model when evaluating mismatch.

4. **Create `experiments/exp10_psf_mismatch/config.yaml` & `plotting.py` & `run_experiment.py`**:
   - Implement full experimental pipeline handling Stages 1–6 (Matched Gaussian baseline, Elliptical mismatch, Asymmetric mismatch, Defocus mismatch, Aberration mismatch, SNR sensitivity matrix, 64-phase grid, and model uncertainty analysis).

5. **Pytest Integration**:
   - Create `tests/test_exp10_psf_mismatch.py` verifying all 5 PSF families, continuous subpixel rendering, mismatch penalties, failure handling, and end-to-end execution.

---

## 5. Audit Conclusion

All prerequisites are understood. Extending `generator/psf.py` and creating `experiments/exp10_psf_mismatch/` will provide a modular, physically sound, and fully reproducible implementation for Experiment 10.
