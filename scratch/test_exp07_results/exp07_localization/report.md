# EXPERIMENT 7 REPORT: COMPARATIVE EVALUATION OF BEACON LOCALIZATION ALGORITHMS

## 1. Experiment Overview & Objective
- **Experiment ID**: exp07_localization
- **Title**: Comparative Evaluation of Beacon Localization Algorithms
- **Research Question**: How do different localization algorithms compare in terms of pixel-level and angular localization accuracy, robustness to image degradation, and computational cost under controlled synthetic camera conditions?
- **Hypothesis**: Intensity-weighted centroid and PSF fitting achieve subpixel accuracy superior to binary centroids under high SNR, but fitting methods exhibit higher failure rates under extreme noise (SNR <= 3 dB).

## 2. Experimental Architecture & ROI Construction
The localization experiment operates directly on cropped fixed-size Regions of Interest (ROI) centered on the ground-truth beacon coordinate $(x_{true}, y_{true})$. Ground-truth coordinates are strictly isolated and not provided as an input or fitting initialization to any algorithm.

```
Synthetic Generator -> Full Image -> Ground-Truth Center -> Fixed ROI Crop (31x31)
                                                                 |
            +--------------------+--------------------+----------+----------+
            |                    |                    |                     |
  Bounding-Box Center    Binary Centroid    Weighted Centroid    Gaussian Fitting    PSF Fitting
```

## 3. Algorithm Mathematical Formulations
1. **Bounding-Box Center**: Thresholds ROI to foreground mask, computes geometric center of foreground bounding box $(x_{min}+x_{max})/2, (y_{min}+y_{max})/2$.
2. **Binary Centroid**: Thresholds ROI, computes arithmetic mean of foreground pixel coordinates $x_c = \frac{1}{N}\sum x_i, y_c = \frac{1}{N}\sum y_i$.
3. **Intensity-Weighted Centroid**: Background-corrected weights $w_i = \max(I_i - B_i, 0)$, $x_c = \frac{\sum w_i x_i}{\sum w_i}, y_c = \frac{\sum w_i y_i}{\sum w_i}$.
4. **Gaussian Fitting**: Non-linear least squares fit of 2D Gaussian $I(x,y) = B + A \exp(-0.5[((x-x0)/\sigma_x)^2 + ((y-y0)/\sigma_y)^2])$ estimating $A, B, x0, y0, \sigma_x, \sigma_y$.
5. **PSF Fitting**: Fits calibrated 2D Gaussian PSF with shape parameters $\sigma_x, \sigma_y$ fixed to nominal calibrated values (2.0 px), estimating amplitude $A$, background $B$, and center $(x0, y0)$.

## 4. Key Findings & Performance Summary

### High SNR (30 dB) Performance
- Lowest Radial RMSE: PSF Fitting (Known PSF) (0.0371 px / 18.08 μrad)

### Severe Noise (0 dB) Performance
- Lowest Radial RMSE: Intensity-Weighted Centroid (1.0227 px / 479.74 μrad)

### Failure Rates & Latency
- Total recorded failures across all trials: 16
- Centroid methods executed in < 0.1 ms per ROI.
- Non-linear least-squares fitting methods required 1.5 - 4.5 ms per ROI.

## 5. Answers to Central Research Questions
- **Noise Influence**: Centroid algorithms degrade gracefully under severe noise; Gaussian fitting suffers non-convergence at low SNR (< 3 dB) due to local minima.
- **Background Estimation**: Intensity-weighted centroid and PSF fitting are highly sensitive to accurate background subtraction. Unsubtracted background offsets bias centroids toward ROI center.
- **PSF Mismatch**: PSF fitting with fixed nominal width exhibits systematic localization bias when actual image PSF width differs from assumed shape.
- **ROI Size**: Increasing ROI size beyond $31 \times 31$ increases background noise contamination for weighted centroids, whereas smaller ROIs (< $15 \times 15$) truncate PSF tails.

## 6. Reproducibility Instructions
To run this experiment:
```bash
python run_experiments.py --experiment 07
```
All raw data, summary tables, paired comparisons, and figures are saved under `results/exp07_localization/` and `reports/figures/exp07_localization/`.
