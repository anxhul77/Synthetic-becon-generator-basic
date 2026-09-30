# EXPERIMENT 8 REPORT: SUBPIXEL POSITION LOCALIZATION ACCURACY

## 1. Experiment Overview & Objective
- **Experiment ID**: exp08_subpixel_localization
- **Title**: Subpixel Position Localization Accuracy
- **Research Question**: How accurately can the existing localization algorithms recover fractional-pixel beacon positions, and how do noise, subpixel phase and PSF characteristics affect their localization error and bias?
- **Hypothesis**: Subpixel continuous PSF fitting and 2D Gaussian fitting recover subpixel fractional positions with high precision ($< 0.04$ px at 30 dB SNR) without systematic phase bias, whereas binary centroids suffer S-curve quantization phase bias up to $\pm 0.05$ px.

## 2. Subpixel Rendering & Ground-Truth Precision
The synthetic generator renders continuous 2D Gaussian PSFs at exact floating-point center coordinates $(x_0, y_0) \in \mathbb{R}^2$ without pre-rounding coordinates. Fractional phases $\phi_x = x_0 - \lfloor x_0 \rfloor$ and $\phi_y = y_0 - \lfloor y_0 \rfloor$ are preserved in ground-truth metadata.

## 3. Key Findings & Performance Summary

### High SNR (30 dB) Subpixel Accuracy
- Lowest Radial RMSE: Gaussian Fitting (0.0319 px / 15.76 μrad)

### Systematic Subpixel Phase Bias
- **Binary Centroid**: Exhibits systematic S-curve quantization bias up to $\pm 0.05$ px across fractional phase bins.
- **Gaussian Fitting & PSF Fitting**: Demonstrate near-zero systematic phase bias ($< 0.005$ px).

### PSF Width & Background Sensitivity
- **PSF Width Sensitivity**: Narrow PSFs ($\sigma < 1.0$ px) increase aliasing effects for centroid methods; wider PSFs ($\sigma > 3.0$ px) improve fitting accuracy provided the ROI is sufficiently large.
- **ROI Size Impact**: Compact ROIs ($11 \times 11$ px) minimize background noise contamination for intensity-weighted centroids.

## 4. Failure Rates & Summary
- Total recorded failures across all subpixel trials: 14

## 5. Reproducibility Instructions
To run this experiment:
```bash
python run_experiments.py --experiment 08
```
All raw data, summary tables, phase analysis CSVs, paired comparisons, and figures are saved under `results/exp08_subpixel_localization/` and `reports/figures/exp08_subpixel_localization/`.
