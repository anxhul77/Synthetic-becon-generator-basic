# FSOC SIMULATOR SIGNAL-TO-NOISE RATIO (SNR) DEFINITION

## 1. DEFINITION OF `snr_db`
In this simulator, `snr_db` is defined as the **Peak Amplitude Signal-to-Noise Ratio (Peak SNR)** of the beacon signal relative to additive sensor noise.

## 2. TYPE OF SNR
It is **Peak Amplitude SNR**, not integrated pulse energy SNR or total signal power SNR.
Specifically, it measures the ratio of the unattenuated peak beacon signal amplitude $A$ above the background baseline to the standard deviation $\sigma_n$ of the Gaussian sensor noise:

$$\text{SNR}_{\text{peak}} = \frac{A}{\sigma_n}$$

Expressing this in decibels (dB):

$$\text{SNR}_{\text{dB}} = 20 \log_{10}\left(\frac{A}{\sigma_n}\right)$$

*Note: The factor of 20 (rather than 10) is used because amplitude $A$ and noise standard deviation $\sigma_n$ are field quantities (voltage / pixel intensity digital numbers DN), matching optical camera sensor conventions.*

## 3. EQUATION CONVERTING CONFIGURED SNR TO NOISE STANDARD DEVIATION ($\sigma_n$)
Given configured peak amplitude $A$ and target $\text{SNR}_{\text{dB}}$, the required sensor noise standard deviation $\sigma_n$ is computed via:

$$\sigma_n = A \cdot 10^{-\frac{\text{SNR}_{\text{dB}}}{20}}$$

### Example Calculations:
- For $A = 150.0$ and $\text{SNR}_{\text{dB}} = 30.0\text{ dB}$:
  $$\sigma_n = 150.0 \cdot 10^{-30.0/20} = 150.0 \cdot 10^{-1.5} \approx 4.7434\text{ DN}$$
- For $A = 150.0$ and $\text{SNR}_{\text{dB}} = 10.0\text{ dB}$:
  $$\sigma_n = 150.0 \cdot 10^{-10.0/20} = 150.0 \cdot 10^{-0.5} \approx 47.4342\text{ DN}$$
- For $A = 150.0$ and $\text{SNR}_{\text{dB}} = 0.0\text{ dB}$:
  $$\sigma_n = 150.0 \cdot 10^{0} = 150.0\text{ DN}$$

## 4. EQUATION USED TO MEASURE SNR AFTERWARD
To independently measure actual SNR from a generated synthetic image:
1. Estimate peak signal amplitude $A_{\text{measured}} = \max(I) - \text{mean}(I_{\text{bg}})$.
2. Measure noise standard deviation $\hat{\sigma}_n$ from a background region $I_{\text{bg}}$ (e.g., $100 \times 100$ pixel window away from beacon):
   $$\hat{\sigma}_n = \sqrt{\frac{1}{M-1} \sum_{i=1}^{M} (I_{\text{bg}, i} - \bar{I}_{\text{bg}})^2}$$
3. Compute measured SNR in dB:
   $$\text{SNR}_{\text{measured, dB}} = 20 \log_{10}\left(\frac{A_{\text{measured}}}{\hat{\sigma}_n}\right)$$

## 5. JUSTIFICATION FOR FSOC BEACON EXPERIMENTS
Peak Amplitude SNR is the standard physical metric in optical communication and acquisition systems because:
1. **Detection Probability ($P_D$)**: Target thresholding ($T = \mu_B + k \sigma_B$) operates on peak pixel intensity exceeding background noise spikes.
2. **Subpixel Centroid Error**: The theoretical Cramér-Rao Lower Bound (CRLB) for subpixel centroid estimation of a Gaussian spot of width $\sigma_{\text{psf}}$ is inversely proportional to Peak SNR:
   $$\text{CRLB}(\sigma_{\hat{x}}) \approx \frac{\sigma_{\text{psf}}}{\text{SNR}_{\text{peak}}}$$
3. **Sensor ADC Model**: Camera sensors measure photon counts converted to digital numbers (DN) per pixel, making peak DN to noise DN ratio the direct operating physical quantity.
