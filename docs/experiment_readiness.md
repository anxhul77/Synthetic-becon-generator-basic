# FSOC Synthetic Beacon Image Generator — Experiment Readiness Assessment

**Date:** 2026-09-26  
**Generator Version:** `1.0.0`  
**Overall Validation Status:** **PASSED** (Analytically and statistically validated within the implemented synthetic model)

---

## Component Readiness Table

| Component | Validated | Ready for Experiment | Limitation / Scope |
| :--- | :---: | :---: | :--- |
| **Camera Geometry** | YES | YES | Ideal pinhole model; zero lens distortion/vignetting. |
| **FOV Calculation** | YES | YES | Derived dynamically from focal length and sensor dimensions. |
| **Gaussian PSF (Isotropic)** | YES | YES | Idealized 2D Gaussian point spread function. |
| **Elliptical Gaussian PSF** | YES | YES | Rotated anisotropic 2D Gaussian optics. |
| **Atmospheric Attenuation** | YES | YES | Beer-Lambert attenuation model only ($T = e^{-\alpha L}$). |
| **Uniform Background** | YES | YES | Constant spatial baseline radiance. |
| **Gradient Background** | YES | YES | Linear spatial gradient model (clipped non-negative). |
| **Gaussian Noise Model** | YES | YES | Additive zero-mean Gaussian sensor noise. |
| **SNR Calibration** | YES | YES | Defined relative to peak signal amplitude $A_{\text{recv}}$. |
| **8-Bit Quantization** | YES | YES | Integer rounding $[0, 255]$ dynamic range clipping. |
| **Float64 Unclipped Mode** | YES | YES | Double-precision raw sensor simulation. |
| **Ground-Truth Metadata** | YES | YES | Full subpixel and angular precision metadata logging. |
| **Seed Reproducibility** | YES | YES | Deterministic RNG behavior across identical seeds. |
| **Atmospheric Turbulence** | NO | NO | Not implemented (future extension point). |
| **Aerosol / Fog Scattering** | NO | NO | Not implemented (future extension point). |
| **Camera Angular Jitter** | NO | NO | Not implemented (future extension point). |
| **Platform Dynamics** | NO | NO | Not implemented (future extension point). |
| **Temporal Beacon Dynamics**| NO | NO | Not implemented (future extension point). |
| **Poisson / Shot Noise** | NO | NO | Not implemented (future extension point). |
| **Salt-and-Pepper Noise** | NO | NO | Not implemented (future extension point). |
| **Multi-Target Clutter** | NO | NO | Not implemented (future extension point). |

---

## Experiment Readiness Approval

The baseline Synthetic Optical Beacon Image Generator v1.0.0 has passed all 36 automated unit tests (`pytest`) and 14 automated validation checks (`validation/run_validation.py`).

**Status for Experiment 1 (Noise Robustness):** **APPROVED**
