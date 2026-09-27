# EXP01 BASELINE OPERATING DEFINITION

This document establishes the official, immutable baseline definitions for the FSOC synthetic camera tracking experimental framework. All subsequent experiments (Experiments 1–18) must adhere to these definitions unless a specific experiment explicitly isolates and varies a parameter.

---

## 1. SNR DEFINITION
- **Type**: Peak Amplitude Signal-to-Noise Ratio (Peak SNR).
- **Formula**:
  $$\text{SNR}_{\text{dB}} = 20 \log_{10}\left(\frac{A}{\sigma_n}\right)$$
  $$\sigma_n = A \cdot 10^{-\frac{\text{SNR}_{\text{dB}}}{20}}$$
- **Baseline Value**: $A = 150.0$, background baseline $B_0 = 10.0$.

---

## 2. NOISE MODEL
- **Type**: Additive Zero-Mean Gaussian Sensor Noise.
- **Distribution**: $N \sim \mathcal{N}(0, \sigma_n^2)$.
- **Implementation**: Independent identically distributed (i.i.d.) random normal samples added to every pixel.

---

## 3. BACKGROUND MODEL
- **Type**: Uniform Baseline Background Illumination.
- **Formula**: $B(x,y) = B_0 = 10.0$ Digital Numbers (DN).
- **Gradient Extension**: $B(x,y) = B_0 + a \cdot x + b \cdot y$ (evaluated in Exp 03).

---

## 4. PSF MODEL
- **Type**: 2D Isotropic Gaussian Point Spread Function.
- **Formula**:
  $$S(x,y) = A \exp\left(-\frac{(x - x_0)^2}{2\sigma_x^2} - \frac{(y - y_0)^2}{2\sigma_y^2}\right)$$
- **Baseline Width**: $\sigma_x = 2.0$ pixels, $\sigma_y = 2.0$ pixels.

---

## 5. CAMERA MODEL & INTRINSICS
- **Authoritative Intrinsics**:
  - Image Width: $1920$ pixels
  - Image Height: $1080$ pixels
  - Focal Length $f_x$: $2000.0$ pixels
  - Focal Length $f_y$: $2000.0$ pixels
  - Principal Point $c_x$: $960.0$ pixels
  - Principal Point $cy$: $540.0$ pixels
- **Auto-Derived FOV**:
  - Horizontal FOV: $\text{FOV}_x = 2 \arctan(1920 / (2 \times 2000)) = 51.2820^\circ$
  - Vertical FOV: $\text{FOV}_y = 2 \arctan(1080 / (2 \times 2000)) = 30.2192^\circ$
- **Frame Rate**: $60.0$ FPS.

---

## 6. PIXEL REPRESENTATION
- **Camera Image Output**: 8-bit unsigned integer `uint8` ($[0, 255]$ DN) clipped to model physical sensor ADC digitization.
- **Analytical Reference Output**: 64-bit double precision `float64` unclipped continuous array for baseline verification.

---

## 7. ATMOSPHERIC MODEL STATUS
- **Status**: **Disabled** for Experiment 01 baseline ($\alpha = 0.0, L = 0.0$, transmittance $T = 1.0$).
- **Activation**: Enabled in Experiment 12 & 13 to evaluate atmospheric attenuation and turbulence.

---

## 8. ATTENUATION STATUS
- **Status**: **Disabled** for Experiment 01 baseline ($I_{\text{received}} = I_0 = A$).
- **Activation**: Enabled in Experiment 12 & 13 ($I_{\text{received}} = I_0 e^{-\alpha L}$).

---

## 9. VALID BEACON REGION (GUARD MARGIN)
- **Valid Coordinates**: $[x_0, y_0] \in [6.0, 1913.0] \times [6.0, 1073.0]$ pixels.
- **Guard Margin**: $3\sigma_{\text{psf}} = 6.0$ pixels from all image boundaries to prevent PSF truncation edge distortion.

---

## 10. GROUND-TRUTH COORDINATE CONVENTION
- **Format**: Subpixel floating-point numbers $(x_0, y_0) \in \mathbb{R}^2$.
- **Origin**: 0-indexed coordinate system with origin $(0.0, 0.0)$ located at the top-left corner pixel center $(0,0)$.
- **Angular Coordinates**: Exact pinhole transformation relative to optical axis:
  $$\theta_{x,\text{true}} = \arctan\left(\frac{x_0 - c_x}{f_x}\right), \quad \theta_{y,\text{true}} = \arctan\left(\frac{y_0 - c_y}{f_y}\right)$$

---

## 11. LOCALIZATION COORDINATE CONVENTION
- **Output**: Subpixel floating-point estimated coordinates $(\hat{x}, \hat{y}) \in \mathbb{R}^2$.
- **Error Metric**:
  $$e_x = \hat{x} - x_0, \quad e_y = \hat{y} - y_0, \quad e_r = \sqrt{e_x^2 + e_y^2}$$
  $$e_{\theta x} = \hat{\theta}_x - \theta_{x,\text{true}}, \quad e_{\theta y} = \hat{\theta}_y - \theta_{y,\text{true}}, \quad e_\theta = \sqrt{e_{\theta x}^2 + e_{\theta y}^2}$$
