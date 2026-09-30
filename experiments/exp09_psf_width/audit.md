# Codebase Audit — Experiment 9: PSF Width and Localization Accuracy

**Date**: September 29, 2026  
**Status**: Completed  
**Target Module**: `experiments/exp09_psf_width`  
**Author**: Senior Computer Vision & FSOC Research Team  

---

## 1. Overview and Audit Purpose

Before implementing **Experiment 9: PSF Width and Localization Accuracy**, an exhaustive codebase audit was conducted to verify compliance with the experimental design, reuse validated components from Experiments 0–8, and confirm the physical integrity of the synthetic beacon generation and subpixel localization pipeline.

The primary objective of Experiment 9 is to evaluate how optical spot width ($\sigma \in \{0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0\}$ px) influences localization accuracy, subpixel phase bias, algorithm robustness, and computational latency across three primary localization estimators:
1. **Intensity-Weighted Centroid** (`IntensityWeightedCentroidLocalization`)
2. **Gaussian Fitting** (`GaussianFittingLocalization`)
3. **PSF Fitting** (`PSFFittingLocalization` with calibrated PSF match)

---

## 2. Relevant Modules and Classes

The existing architecture provides a modular physical pipeline and localization framework. The key audited components are:

| Module / File Path | Class / Function | Reusability & Responsibility |
| :--- | :--- | :--- |
| `generator/generator.py` | `SyntheticBeaconGenerator` | Core physical frame generator. Evaluates PSF at continuous fractional subpixel coordinates $(x_0, y_0)$ without position rounding. Supports `sigma_x`, `sigma_y`, background models, and SNR noise injection. |
| `generator/psf.py` | `GaussianPSF` | 2D continuous isotropic Gaussian PSF model ($I(x,y) = A \exp(-[(x-x_0)^2 + (y-y_0)^2]/(2\sigma^2))$). Supports arbitrary floating-point $\sigma$. |
| `generator/camera.py` | `PinholeCamera` | Pinhole camera intrinsic model ($f_x=f_y=2000$ px, $c_x=960, c_y=540$). Calculates exact non-approximated angular errors in $\mu\text{rad}$. |
| `experiments/exp07_localization/src/roi_extractor.py` | `ROIExtractor` | Ground-truth centered subpixel ROI extractor ($31\times31$ px default). Ensures spatial bounds safety without leakage. |
| `experiments/exp07_localization/src/intensity_weighted_centroid.py` | `IntensityWeightedCentroidLocalization` | Background-corrected non-negative weight centroid. Robust to near-zero background residual weights. |
| `experiments/exp07_localization/src/gaussian_fitting.py` | `GaussianFittingLocalization` | 2D non-linear Gaussian least-squares fitter estimating amplitude, center $(x_0, y_0)$, widths $(\sigma_x, \sigma_y)$, and baseline offset ($B$). |
| `experiments/exp07_localization/src/psf_fitting.py` | `PSFFittingLocalization` | Calibrated PSF model fitter fixing PSF width to nominal calibration ($\sigma$) or estimating width if configured. |
| `experiments/exp07_localization/src/localization_evaluation.py` | `LocalizationEvaluator` | Evaluates RMSE, 2D bias, success rate, angular error ($\mu\text{rad}$), bootstrap CIs, paired differences, and latency metrics. |
| `experiments/exp08_subpixel_localization/src/phase_grid.py` | `generate_phase_grid` | 64-phase subpixel grid $(\phi_x, \phi_y \in \{0, 0.125, \dots, 0.875\})$ for subpixel grid phase sensitivity analysis. |

---

## 3. Mandatory Audit Checklist & Verification Results

| Audit Check | Status | Verification Detail |
| :--- | :--- | :--- |
| **1. Genuine Fractional Subpixel Spot Rendering** | **VERIFIED** | `BeaconSignal.render` and `GaussianPSF.render` evaluate continuous 2D Gaussian functions at exact floating-point $(x_0, y_0)$. No grid rounding or integer truncation occurs. |
| **2. Continuous PSF Evaluation** | **VERIFIED** | `GaussianPSF` evaluates analytical exponential equations over full pixel meshgrids for any positive $\sigma$. |
| **3. Identical ROI per Trial Across Estimators** | **VERIFIED** | All three estimators receive the exact same generated $31\times 31$ image ROI array extracted by `ROIExtractor`. |
| **4. Distinct Model Formulations for Fitter Algorithms** | **VERIFIED** | `GaussianFittingLocalization` fits 6 parameters including $(\sigma_x, \sigma_y)$, whereas `PSFFittingLocalization` fixes $(\sigma_x, \sigma_y) = \sigma_{\text{calibrated}}$ and fits 4 parameters $(A, x_0, y_0, B)$. |
| **5. Explicit Failure Recording** | **VERIFIED** | Optimizer non-convergence, boundary overflow, and non-finite parameters return explicit `LocalizationResult(success=False, failure_reason=...)` records logged to `failures.csv`. |
| **6. Identical Evaluated Images** | **VERIFIED** | Images are generated once per seed/trial and shared across all three localization methods via paired evaluation. |
| **7. Consistent Camera & Coordinate Conventions** | **VERIFIED** | Standard 0-indexed pixel coordinates with origin at top-left pixel center $(0.0, 0.0)$, matching camera intrinsics ($c_x=960.0, c_y=540.0$). |
| **8. Out-of-Memory (OOM) Protection for Large Datasets** | **VERIFIED** | Trial results process sequentially in configurable execution batches, streaming metrics directly to CSV files without retaining raw numpy frames in RAM. |

---

## 4. Signal Physics & Energy Scaling Considerations

1. **Fixed Peak-Amplitude vs Fixed Integrated Energy**:
   - In the continuous 2D Gaussian PSF, integrated signal energy above background is $E = 2\pi A \sigma^2$.
   - Holding peak amplitude constant ($A = 150.0$) while varying $\sigma \in \{0.5, \dots, 4.0\}$ scales total signal energy quadratically with $\sigma$.
   - **Resolution**: The primary experiment evaluates fixed peak amplitude ($A=150.0$). An optional fixed-energy sensitivity experiment is implemented using energy scaling $A(\sigma) = A_{\text{ref}} \frac{\sigma_{\text{ref}}^2}{\sigma^2}$ (with $\sigma_{\text{ref}} = 2.0$ px) to isolate spot geometry from SNR/energy effects.

2. **Pixel Sampling at Small PSF Widths ($\sigma = 0.5$ px)**:
   - At $\sigma = 0.5$ px, $>95\%$ of beacon intensity is concentrated in a $3\times3$ pixel region, introducing pixel discretization aliasing and subpixel grid phase dependency.
   - **Resolution**: Controlled subpixel phase grid ($8\times 8 = 64$ phase steps) is evaluated across all $\sigma$ levels.

3. **Spatial Windowing / ROI Truncation ($\sigma = 4.0$ px)**:
   - For $\sigma = 4.0$ px, the $99.7\%$ energy radius ($3\sigma$) extends $12$ pixels from the center ($24\times24$ px footprint). A $31\times31$ px ROI captures $>99.9\%$ of signal energy. An ROI size sensitivity matrix ($11\times11$ to $41\times41$ px) validates truncation thresholds.

---

## 5. Required Extensions and Additions

No core generator architectural rewrites are required. The following modular components will be created under `experiments/exp09_psf_width/`:

1. `config.yaml`: Experiment configuration schema for Exp 9.
2. `src/energy_scaler.py`: Amplitude scaling helper for fixed-amplitude vs fixed-energy regimes.
3. `src/plotting.py`: Publication-quality visualization generator for Figures 1–12.
4. `src/run_experiment.py`: Main Experiment 9 execution runner class `Exp09PSFWidth` inheriting from `BaseExperiment`.
5. `tests/test_exp09_psf_width.py`: Pytest suite for Exp 9 verification.

---

## 6. Audit Conclusion

The existing codebase fully supports Experiment 9. Pipeline components, continuous subpixel rendering, coordinate transformations, and localization estimators are verified as modular, mathematically sound, and ready for Experiment 9 execution.
