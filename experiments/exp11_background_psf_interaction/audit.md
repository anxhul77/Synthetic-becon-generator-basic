# EXPERIMENT 11 AUDIT — BACKGROUND AND PSF INTERACTION

## 1. Audit Overview & Research Objectives
This audit verifies codebase compatibility, component reuse, and architectural design for **Experiment 11: Background and PSF Interaction**.
The objective is to quantify how optical spot width ($\sigma \in \{1.0, 2.0, 3.0, 4.0\}$ px), background conditions ($B \in \{10, 50, 100, 200\}$ DN; uniform and gradient types), and signal-to-noise ratio ($\text{SNR} \in \{5, 10, 15, 20\}$ dB) jointly influence subpixel beacon localization accuracy, systematic bias, fitting convergence, and latency.

---

## 2. Reused Validated Components

### 2.1 Experiment 3 — Background Models & Suppression
- **Uniform Background**: $B(x, y) = B_0$, implemented via `UniformBackground` (`generator/background.py`).
- **Gradient Backgrounds**: $B(x, y) = B_0 + a \cdot x + b \cdot y$, implemented via `GradientBackground` (`generator/background.py`).
  - *Horizontal Gradient*: $a = \Delta_x / (W - 1)$, $b = 0$.
  - *Vertical Gradient*: $a = 0$, $b = \Delta_y / (H - 1)$.
  - *2D Gradient*: $a = \Delta_x / (W - 1)$, $b = \Delta_y / (H - 1)$.
- **Background Suppression Filters**: Reused from `processing/background_suppression.py`:
  - `apply_none`: Baseline un-filtered ROI image.
  - `apply_gaussian_sub`: Rolling Gaussian background estimation and subtraction ($\sigma = 15.0$).
  - `apply_tophat`: Morphological top-hat background suppression (structuring element radius $r = 7$).

### 2.2 Experiment 9 — Isotropic Gaussian PSF Width
- **Gaussian PSF Model**: `GaussianPSF` (`generator/psf.py`) supporting arbitrary standard deviation $\sigma_x = \sigma_y = \sigma$.
- **Continuous Fractional Position Rendering**: `BeaconSignal` (`generator/beacon.py`) rendering subpixel beacon profiles with normalized energy conservation.
- **Pinhole Camera Intrinsics**: `PinholeCamera` (`generator/camera.py`) converting subpixel errors $(e_x, e_y)$ into exact angular errors in microradians ($\mu\text{rad}$).

### 2.3 Experiment 10 — Estimator Architecture & Infrastructure
- **Base Experiment Rig**: Reused `BaseExperiment` (`experiments/base_experiment.py`) for reproducible seed schedules, incremental serialization, summary statistics, and paired statistical comparisons.
- **Zero Ground-Truth Leakage**: Estimator initializations derive strictly from image crop statistics (geometric ROI center and border background median/mean); ground-truth coordinates $(x_{\text{true}}, y_{\text{true}})$ are used solely as oracle ROI extraction targets and error evaluation references.

### 2.4 Experiments 7 & 8 — Evaluated Estimators
1. **Intensity-Weighted Centroid**: `IntensityWeightedCentroidLocalization` (`experiments/exp07_localization/src/intensity_weighted_centroid.py`) with background baseline subtraction.
2. **Gaussian Fitting**: `GaussianFittingLocalization` (`experiments/exp07_localization/src/gaussian_fitting.py`) non-linear Levenberg-Marquardt optimizer fitting unconstrained isotropic 2D Gaussian.
3. **PSF Fitting**: `PSFAwareFittingLocalization` (`experiments/exp10_psf_mismatch/src/psf_aware_fitting.py`) calibrated Gaussian fitter initialized with the exact configured PSF width $\sigma$.

---

## 3. Codebase Readiness Assessment

| Requirement | Codebase Status | Reused Component / File Path | Modifications Required |
| :--- | :---: | :--- | :--- |
| **Configurable PSF Width** | Verified | `GaussianPSF` in `generator/psf.py` | None |
| **Multiple Background Types** | Verified | `generator/background.py` and `generator/generator.py` | Extended `generate_frame` for `horizontal`, `vertical`, `two_dimensional` background strings |
| **Peak-Amplitude SNR Model** | Verified | `GaussianNoise` in `generator/noise.py` | None |
| **Paired Image Evaluation** | Verified | `SyntheticBeaconGenerator` deterministic seed schedule | Single generated frame passed to all 3 estimators per trial |
| **Subpixel Phase Grid** | Verified | `generate_controlled_phase_grid` (`exp08_subpixel_localization`) | Reused $8 \times 8$ phase grid step generator |
| **Factorial & ANOVA Analysis** | Missing | `experiments/exp11_background_psf_interaction/src/factorial_analysis.py` | Implemented 2-way and 3-way interaction contrasts and linear model ANOVA |

---

## 4. Architectural Summary
All primary evaluations isolated the interaction between background level, background type, SNR, and PSF width using isotropic Gaussian PSFs. Estimator evaluation is strictly paired, deterministic, and free of ground-truth leakage. Output artifacts match the experiment pipeline specification.
