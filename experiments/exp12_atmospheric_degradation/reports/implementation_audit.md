# EXPERIMENT 12 — ATMOSPHERIC DEGRADATION IMPLEMENTATION AUDIT

## 1. Executive Summary & Audit Objective

This document provides a comprehensive audit of the existing FSOC synthetic beacon generator codebase prior to implementing **Experiment 12: Atmospheric Degradation**. The objective is to evaluate existing atmospheric, optical, sensor, detection, and localization components, identify gaps, and design minimal, non-breaking extensions for modeling Beer–Lambert attenuation, atmospheric turbulence (scintillation, beam wander, PSF broadening), and atmospheric scattering (halo energy redistribution).

---

## 2. Audit of Existing Codebase Components

### 2.1 Atmospheric Model (`generator/atmosphere.py`)
- **Current State**: Implements basic Beer–Lambert attenuation:
  $$I_{\text{received}} = I_0 \cdot \exp(-\alpha \cdot L)$$
  where $\alpha$ is `attenuation_alpha` ($\text{km}^{-1}$) and $L$ is `range_km` ($\text{km}$).
- **Transmittance**: $T(L) = \exp(-\alpha \cdot L)$.
- **Gaps Identified for Exp 12**:
  - Lacks atmospheric turbulence modeling (irradiance scintillation $\sigma_I^2$, beam wander spatial displacement $(\Delta x, \Delta y)$, and spot broadening $\sigma_{\text{blur}}$).
  - Lacks atmospheric scattering modeling (spatial energy redistribution halo $I_{\text{scattered}} = (1-\eta)I_{\text{direct}} + \eta I_{\text{halo}}$).

### 2.2 Image Formation Pipeline (`generator/generator.py`)
- **Current State**: `SyntheticBeaconGenerator.generate_frame` follows the sequence:
  $$\text{Beacon Ground Truth} \rightarrow \text{Beer–Lambert Attenuation} \rightarrow \text{PSF Rendering} \rightarrow \text{Background} \rightarrow \text{Sensor Noise} \rightarrow \text{Clipping/Quantization}$$
- **Sensor Noise**: `GaussianNoise` applies peak-amplitude SNR:
  $$\sigma_n = A_{\text{attenuated}} \cdot 10^{-\text{SNR}_{\text{dB}}/20}$$
- **Quantization & Saturation**: Computes exact pixel saturation fractions and bit-depth clipping (8-bit uint8 or 64-bit float).

### 2.3 Camera & PSF Optics (`generator/camera.py`, `generator/psf.py`)
- **Pinhole Camera**: $f_x = f_y = 2000.0$ px, principal point $(c_x, c_y) = (960.0, 540.0)$ px, resolution $1920 \times 1080$ px.
- **PSF Models**: Gaussian ($I(r) \propto \exp(-r^2 / 2\sigma^2)$) and Elliptical Gaussian.

### 2.4 Localization & Detection Pipeline (`experiments/exp07_localization`, `exp06_classical_vs_ai`)
- **Subpixel Estimators**:
  1. Intensity-Weighted Centroid
  2. Gaussian Fitting (Unconstrained 2D LM Gaussian Fitter)
  3. PSF Fitting (Model-matched calibrated Gaussian Fitter)
- **Full-Frame Detection**: Adaptive thresholding + Connected Component Extraction + ROI candidate filtering.

---

## 3. Mandatory Experimental Stages for Experiment 12

1. **Stage 12A — Distance-Dependent Attenuation**:
   - Propagation distances: $L \in \{0, 1, 2, 5, 10, 15, 20\}\text{ km}$ at fixed $\alpha = 0.0001\text{ km}^{-1}$.
   - Fixed pre-propagation noise floor to isolate true range attenuation effects.

2. **Stage 12B — Attenuation Sensitivity**:
   - Attenuation coefficients: $\alpha \in \{0, 0.00005, 0.0001, 0.0002, 0.0005, 0.001\}\text{ km}^{-1}$ across distances $L \in \{1, 5, 10\}\text{ km}$.

3. **Stage 12C — Atmospheric Turbulence**:
   - Turbulence strengths: None ($0.0$), Weak ($0.1$), Moderate ($0.25$), Strong ($0.5$).
   - Scintillation ratio variance $\sigma_I = 0.2 \cdot \text{strength}$.
   - Beam wander displacement std dev $\sigma_{\text{wander}} = 2.5 \cdot \text{strength}$ [px].
   - Spot broadening $\sigma_{\text{eff}} = \sqrt{\sigma_0^2 + (1.5 \cdot \text{strength})^2}$ [px].

4. **Stage 12D — Atmospheric Scattering**:
   - Scattering fraction: $\eta \in \{0, 0.05, 0.1, 0.2, 0.4\}$.
   - Halo widths: $\sigma_{\text{halo}} \in \{5, 10, 20\}\text{ px}$.
   - Energy redistribution equation: $I_{\text{scattered}} = (1-\eta)I_{\text{direct}} + \eta I_{\text{halo}}$.

5. **Stage 12E — Combined Atmospheric Degradation**:
   - Factorial matrix combining Distance $\times$ Attenuation $\times$ Turbulence $\times$ Scattering.

---

## 4. Minimal Proposed Extensions

- Add `EnhancedAtmosphericModel` in `experiments/exp12_atmospheric_degradation/src/atmospheric_models.py` incorporating Beer–Lambert attenuation, turbulence (scintillation, beam wander, spot broadening), and scattering halo energy redistribution.
- Add `FullFrameBeaconDetector` in `experiments/exp12_atmospheric_degradation/src/detector.py` for thresholding, connected component extraction, candidate filtering, and $P_D / P_{\text{FA}}$ metrics.
- Add `Exp12AtmosphericDegradation` runner extending `BaseExperiment`.
