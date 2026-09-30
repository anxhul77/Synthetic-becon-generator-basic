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
- Lowest Radial RMSE: Gaussian Fitting (0.0354 px / 17.52 μrad)

### Systematic Subpixel Phase Bias
- **Binary Centroid**: Exhibits systematic S-curve quantization bias up to $\pm 0.05$ px across fractional phase bins.
- **Gaussian Fitting & PSF Fitting**: Demonstrate near-zero systematic phase bias ($< 0.005$ px).

### PSF Width & Background Sensitivity
- **PSF Width Sensitivity**: Narrow PSFs ($\sigma < 1.0$ px) increase aliasing effects for centroid methods; wider PSFs ($\sigma > 3.0$ px) improve fitting accuracy provided the ROI is sufficiently large.
- **ROI Size Impact**: Compact ROIs ($11 \times 11$ px) minimize background noise contamination for intensity-weighted centroids.

## 4. Failure Rates & Summary
- Total recorded failures across all subpixel trials: 148

## 5. Reproducibility Instructions
To run this experiment:
```bash
python run_experiments.py --experiment 08
```
All raw data, summary tables, phase analysis CSVs, paired comparisons, and figures are saved under `results/exp08_subpixel_localization/` and `reports/figures/exp08_subpixel_localization/`.
Executive Summary & Central Answers
Subpixel Recovery Accuracy:

Gaussian Fitting and PSF Fitting (Known PSF) successfully recover continuous subpixel beacon coordinates with 0.0354 px radial RMSE (corresponding to an angular RMSE of 17.52 $\mu\text{rad}$) at 30 dB SNR.
Intensity-Weighted Centroid achieves 0.2227 px ($108.34\ \mu\text{rad}$) subpixel accuracy at 30 dB SNR.
Systematic Subpixel Phase Bias:

Binary Centroid suffers from a systematic S-curve quantization phase bias of up to $\pm 0.052\text{ px}$ across fractional phase bins $\phi \in [0, 1)$. Thresholding pixel intensities into binary masks pulls the estimated centroid toward the integer grid.
Gaussian Fitting & PSF Fitting demonstrate near-zero systematic subpixel phase bias ($< 0.005\text{ px}$) because continuous non-linear least-squares fitting models the spatial Gaussian profile directly.
PSF Width & Sampling Sensitivity:

Narrow PSFs ($\sigma = 0.5\text{ px}$) cause spatial aliasing, degrading centroid subpixel error to 0.68 px.
Wider PSFs ($\sigma = 2.0 - 4.0\text{ px}$) spread spatial energy smoothly across pixels, allowing subpixel fitting algorithms to achieve optimal sub-0.04 px recovery.
Complete Statistical Breakdown
Parameter / Sub-Experiment	Description	Volume / Measure
Total Unique Synthetic Images	Generated at continuous float coordinates $(x_0, y_0) \in \mathbb{R}^2$	1,490 paired images
Total Algorithm Evaluations	Across 5 localization algorithms on identical ROIs	7,450 evaluations
Exp 8A (Random SNR Sweep)	Random $\phi_x, \phi_y \sim U(0,1)$ across 9 SNR levels	900 evaluations
Exp 8B (Controlled Phase Grid)	64 controlled phase grid combinations $(\phi_x, \phi_y) \in {0, 0.125, \dots, 0.875}^2$	6,400 evaluations
Exp 8C (PSF Width Sensitivity)	$\sigma \in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]\text{ px}$	700 evaluations
Exp 8D (Background Sensitivity)	Uniform background levels $B \in [0, 10, 50, 100, 200, 500]$	600 evaluations
Exp 8E (ROI-Size Sensitivity)	Window sizes $[11, 15, 21, 31, 41]\text{ px}$	500 evaluations
Subpixel Performance Summary at 30 dB SNR:
Algorithm	Radial RMSE (px)	95% Bootstrap CI (px)	Angular RMSE ($\mu\text{rad}$)	Systematic Phase Bias	Mean Latency (ms)
Gaussian Fitting	0.0354	[0.0293, 0.0399]	17.52	$<0.005$ px	5.52 ms
PSF Fitting (Known PSF)	0.0355	[0.0294, 0.0400]	17.56	$<0.005$ px	3.62 ms
Intensity-Weighted Centroid	0.2227	[0.1955, 0.2478]	108.34	$\approx 0.015$ px	0.19 ms
Binary Centroid	0.2758	[0.2309, 0.3207]	132.26	$\mathbf{\pm 0.052}$ px (S-curve)	0.09 ms
Bounding-Box Center	3.1240	[2.5181, 3.7112]	1504.56	$\approx 0.118$ px	0.20 ms
Generated Output Files & Figures
📁 Results Directory: 

results/exp08_subpixel_localization/



raw_data.csv


summary.csv


phase_analysis.csv


paired_comparison.csv


localization_failures.csv


experiment_config.yaml


report.md
🖼️ Figures Directory: 

reports/figures/exp08_subpixel_localization/

