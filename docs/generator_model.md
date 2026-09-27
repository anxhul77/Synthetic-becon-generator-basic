# FSOC Synthetic Optical Beacon Image Generator — Mathematical & Physical Model Specification

**Research Title:** Development of an AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile Free Space Optical Communication (FSOC) Terminals  
**Module Version:** `1.0.0`  
**Status:** Analytically and statistically validated within the implemented synthetic model.

---

## 1. Image Formation Pipeline

The synthetic optical beacon image generator implements a discrete baseline image-formation pipeline:

$$\text{Beacon Ground Truth} \longrightarrow \text{Atmospheric Attenuation} \longrightarrow \text{Optical PSF} \longrightarrow \text{Background Illumination} \longrightarrow \text{Sensor Gaussian Noise} \longrightarrow \text{Quantization / Clipping} \longrightarrow \text{Synthetic Image}$$

The governing image-formation equation for spatial pixel location $(x, y)$ is:

$$I(x, y) = \mathcal{Q}\left( \text{clip}\left[ A_{\text{recv}} \cdot \text{PSF}(x - x_0, y - y_0) + B(x, y) + N(0, \sigma_n^2), 0, I_{\max} \right] \right)$$

where:
- $A_{\text{recv}} = A_0 \cdot T$ is the attenuated peak signal amplitude (digital counts).
- $\text{PSF}(x - x_0, y - y_0)$ is the normalized spatial point spread function centered at ground-truth subpixel location $(x_0, y_0)$.
- $B(x, y)$ is the background illumination radiance array.
- $N(0, \sigma_n^2)$ is independent additive white Gaussian sensor noise.
- $\text{clip}[v, 0, I_{\max}]$ constrains radiance values to the physical dynamic range ($I_{\max} = 2^b - 1$ for $b$-bit depth).
- $\mathcal{Q}(\cdot)$ denotes discrete spatial integer rounding (for uint8 mode) or float64 pass-through.

---

## 2. Pinhole Camera Geometry

The baseline optical geometry is governed by an ideal pinhole camera model without lens distortion:

### Intrinsics Matrix
$$\mathbf{K} = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$$

### Pixel-to-Angle Conversion
Given subpixel coordinates $(u, v)$, the angular direction $(\theta_x, \theta_y)$ relative to the optical axis in radians is:

$$\theta_x = \arctan\left( \frac{u - c_x}{f_x} \right)$$

$$\theta_y = \arctan\left( \frac{v - c_y}{f_y} \right)$$

### Angle-to-Pixel Conversion
Given angular coordinates $(\theta_x, \theta_y)$ in radians, the pixel projection $(u, v)$ is:

$$u = c_x + f_x \tan(\theta_x)$$

$$v = c_y + f_y \tan(\theta_y)$$

### Field of View (FOV)
The full horizontal and vertical fields of view in degrees are dynamically computed from sensor dimensions $(W, H)$ and focal lengths $(f_x, f_y)$:

$$\text{FOV}_x = 2 \arctan\left( \frac{W}{2 f_x} \right) \times \frac{180^\circ}{\pi}$$

$$\text{FOV}_y = 2 \arctan\left( \frac{H}{2 f_y} \right) \times \frac{180^\circ}{\pi}$$

---

## 3. Point Spread Function (PSF) Models

### 2D Isotropic Gaussian PSF
$$S_{\text{isotropic}}(x, y) = A_{\text{recv}} \exp\left( -\frac{(x - x_0)^2}{2 \sigma_x^2} - \frac{(y - y_0)^2}{2 \sigma_y^2} \right)$$

For isotropic optics, $\sigma_x = \sigma_y = \sigma$.

### 2D Anisotropic / Rotated Gaussian PSF
For non-symmetric optical aberration or astigmatism rotated by angle $\theta$:

$$\begin{bmatrix} x_{\text{rot}} \\ y_{\text{rot}} \end{bmatrix} = \begin{bmatrix} \cos\theta & \sin\theta \\ -\sin\theta & \cos\theta \end{bmatrix} \begin{bmatrix} x - x_0 \\ y - y_0 \end{bmatrix}$$

$$S_{\text{anisotropic}}(x, y) = A_{\text{recv}} \exp\left( -\frac{x_{\text{rot}}^2}{2 \sigma_x^2} - \frac{y_{\text{rot}}^2}{2 \sigma_y^2} \right)$$

---

## 4. Atmospheric Attenuation Model

The current atmospheric model implements **Beer-Lambert optical power attenuation only**:

$$T = \exp\left( -\alpha L \right)$$

$$A_{\text{recv}} = A_0 \cdot T$$

where:
- $\alpha$ is the atmospheric attenuation coefficient ($\text{km}^{-1}$).
- $L$ is the optical propagation link range ($\text{km}$).
- $T \in (0, 1]$ is the total atmospheric transmittance.

> **CRITICAL SCIENTIFIC NOTE:**  
> The current baseline AtmosphericModel handles **attenuation only**. Atmospheric turbulence (beam wander, scintillation, phase structure constant $C_n^2$), Mie/Rayleigh aerosol scattering, fog degradation, rain extinction, and refractive Index gradient fluctuations are **NOT currently implemented** in baseline v1.0.0. The `condition` input string (e.g., `"clear"`, `"fog"`) serves as configuration metadata only.

---

## 5. Background Illumination Models

### Uniform Background
$$B_{\text{uniform}}(x, y) = B_0$$

### Gradient Background
$$B_{\text{gradient}}(x, y) = \max\left( 0, B_0 + a \cdot x + b \cdot y \right)$$

where $B_0$ is the baseline illumination, and $a, b$ represent horizontal and vertical linear spatial intensity gradients. Radiance is clipped at 0.0 to prevent physically non-viable negative illumination.

---

## 6. Sensor Noise Model & SNR Definition

Additive White Gaussian Noise (AWGN) models thermal and sensor readout noise:

$$N \sim \mathcal{N}(0, \sigma_n^2)$$

The Signal-to-Noise Ratio (SNR) in dB is defined relative to the peak attenuated beacon signal amplitude $A_{\text{recv}}$:

$$\text{SNR}_{\text{dB}} = 20 \log_{10}\left( \frac{A_{\text{recv}}}{\sigma_n} \right)$$

Solving for noise standard deviation $\sigma_n$:

$$\sigma_n = A_{\text{recv}} \cdot 10^{-\frac{\text{SNR}_{\text{dB}}}{20}}$$

---

## 7. Quantization and Clipping Model

$$\text{Image}_{\text{quantized}} = \begin{cases} \text{round}\left( \text{clip}(I(x,y), 0, 255) \right) \in \mathbb{U}^8 & \text{if bit\_depth = 8} \\ I(x,y) \in \mathbb{F}^{64} & \text{if bit\_depth = 64} \end{cases}$$

---

## 8. Ground-Truth Metadata Specification

Each generated frame output returns a complete, immutable ground-truth dictionary containing:

- `image_id`: Unique frame identifier (UUIDv4).
- `seed`: Deterministic Random Number Generator seed used.
- `generator_version`: `"1.0.0"`.
- `width`, `height`: Image resolution in pixels.
- `x_true`, `y_true`: Exact true subpixel target centroid $(x_0, y_0)$.
- `theta_x_true`, `theta_y_true`: Exact true angular target direction $(\theta_x, \theta_y)$ in radians.
- `amplitude`: Unattenuated beacon peak source amplitude $A_0$.
- `attenuated_amplitude`: Received peak beacon amplitude $A_{\text{recv}}$.
- `background`, `background_type`: Background baseline intensity and model type.
- `sigma_x`, `sigma_y`: PSF widths in pixels.
- `snr_db`, `sigma_n`: Configured SNR in dB and calculated noise standard deviation $\sigma_n$.
- `psf_type`, `noise_type`: Selected PSF and noise model identifiers.
- `range_km`, `attenuation_alpha`, `transmittance`, `atmospheric_condition`: Propagation parameters.
- `fx`, `fy`, `cx`, `cy`, `camera_fps`: Authoritative pinhole camera intrinsics.

---

## 9. Model Assumptions and Limitations

1. **Optical Model:** Ideal pinhole geometry without radial or tangential lens distortion, coma, or vignetting.
2. **PSF Model:** Ideal Gaussian energy distribution; does not account for diffraction rings (Airy disk) or pupil aperture obscuration.
3. **Atmospheric Model:** Pure Beer-Lambert attenuation; zero beam wander, zero wavefront distortion, zero scintillation.
4. **Noise Model:** Pure AWGN; Poisson photon shot noise, Dark Current Non-Uniformity (DCNU), Photo Response Non-Uniformity (PRNU), and impulse noise are not included in baseline.
5. **Border Truncation:** Beacons placed within $3\sigma$ of the image border experience edge clipping, introducing subpixel centroid shift if uncompensated.
