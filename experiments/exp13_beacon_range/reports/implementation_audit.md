# EXPERIMENT 13 — BEACON RANGE AND TRACKER OPERATING ENVELOPE IMPLEMENTATION AUDIT

## 1. Executive Summary & Audit Objective

This document presents the implementation audit for **Experiment 13: Beacon Range and Tracker Operating Envelope**. The objective is to audit existing FSOC image generation, optical link, camera geometry, atmospheric degradation, detection, and localization components, and outline minimal, non-breaking extensions required to model received optical power, beam expansion, spot-size variation, and empirical operating-envelope classification over range $L \in \{1, 2, 5, 10, 20\}\text{ km}$.

---

## 2. Codebase Audit & Component Reusability

### 2.1 Pinhole Camera Geometry (`generator/camera.py`)
- **Existing Capabilities**: Models focal length $f_x = f_y = 2000.0$ px, principal point $(c_x, c_y) = (960.0, 540.0)$ px, resolution $1920 \times 1080$ px.
- **Angular Conversion**: Exact arctan pinhole equations:
  $$\theta_x = \tan^{-1}\left(\frac{u - c_x}{f_x}\right), \quad \theta_y = \tan^{-1}\left(\frac{v - c_y}{f_y}\right)$$
- **Lateral Displacement Mapping**: For lateral displacement $d$ at distance $L$, angular offset is $\theta = \tan^{-1}(d / L)$.

### 2.2 Atmospheric Degradation (`experiments/exp12_atmospheric_degradation/src/atmospheric_models.py`)
- **Beer-Lambert Attenuation**: Transmittance $T(L) = \exp(-\alpha \cdot L)$.
- **Turbulence Model**: Scintillation amplitude noise, beam wander spatial displacement $(\Delta x, \Delta y)$, and spot broadening $\sigma_{\text{eff}} = \sqrt{\sigma_0^2 + \sigma_{\text{blur}}^2}$.
- **Scattering Model**: Spatial energy redistribution halo $I_{\text{scattered}} = (1-\eta)I_{\text{direct}} + \eta I_{\text{halo}}$.

### 2.3 Optical Link Power & Beam Spreading (`experiments/exp13_beacon_range/src/optical_power.py`)
- **Gaussian Beam Expansion**: $w(L) = w_0 \sqrt{1 + (L / z_R)^2}$ where $z_R = \pi w_0^2 / \lambda$.
- **Captured Power**: $P_{\text{captured}}(L) = P_0 \cdot \left[1 - \exp\left(-2 (D_{\text{rx}} / 2)^2 / w(L)^2\right)\right]$.
- **Received Amplitude Mapping**: $A_{\text{received}}(L) = A_0 \cdot \frac{P_{\text{captured}}(L)}{P_{\text{captured}}(L_0)} \cdot T(L)$.

### 2.4 Detector & Localization (`experiments/exp12_atmospheric_degradation/src/detector.py`, `exp07_localization`)
- **Detector**: `FullFrameBeaconDetector` with threshold $T = \mu_{\text{bg}} + 3.5 \sigma_{\text{bg}}$, connected components, and candidate matching gate.
- **Subpixel Estimators**: Intensity-Weighted Centroid, Gaussian Fitting, PSF Fitting.

---

## 3. Mandatory Experimental Stages for Experiment 13

1. **Stage 13A — Geometric Range**: Camera pinhole mapping vs propagation distance $L \in \{1, 2, 5, 10, 20\}\text{ km}$ under fixed pixel position and lateral displacement scenarios.
2. **Stage 13B — Optical Power vs Range**: Beam waist expansion $w(L)$ and captured optical power $P_{\text{received}}(L)$.
3. **Stage 13C — Spot-Size Variation**: Distance-dependent apparent spot width $\sigma(L)$ at constant signal amplitude.
4. **Stage 13D — Atmospheric Range**: Attenuation, turbulence, and scattering across 5 range scenarios (No atmosphere, Attenuation only, Turbulence only, Scattering only, Combined).
5. **Stage 13E — Combined Range Experiment**: Joint evaluation across range $L \in \{1, 2, 5, 10, 20\}\text{ km}$.
6. **Stage 13F — Operating Envelope Analysis**: Classifies compliant distances satisfying $P_D \ge 0.95$, $P_{\text{FA}} \le 0.01$, $\text{RMSE}_\theta \le 100\ \mu\text{rad}$ with 95% confidence bounds.
