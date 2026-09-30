# EXPERIMENT 13 REPORT: BEACON RANGE AND OPERATING ENVELOPE

## 1. Executive Summary & Research Objectives
- **Experiment ID**: exp13_beacon_range
- **Title**: Beacon Range and Operating Envelope Experiment
- **Primary Objective**: Investigate how beacon propagation distance ($L \in [1, 20]\text{ km}$) affects received optical power $P_{\text{received}}(L)$, Gaussian beam waist expansion $w(L)$, apparent spot size, detection probability $P_D$, and angular pointing accuracy $\text{RMSE}_\theta$, establishing the empirical operating envelope of the tracker.

## 2. Stage 13E: Combined Range & Operating Envelope Summary Table

| Range (km) | Beam Radius w(L) (m) | Transmittance T(L) | Received Amplitude (DN) | Gaussian Fit P_D (%) | Angular Error RMSE (μrad) | Operating Envelope Compliance |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1.0 km | 0.051 m | 0.9999 | 150.2 DN | 100.0% | 17.68 μrad | PASSED (Compliant) |
| 2.0 km | 0.054 m | 0.9998 | 143.8 DN | 100.0% | 17.50 μrad | PASSED (Compliant) |
| 5.0 km | 0.070 m | 0.9995 | 111.8 DN | 100.0% | 19.21 μrad | PASSED (Compliant) |
| 10.0 km | 0.111 m | 0.9990 | 59.2 DN | 100.0% | 18.20 μrad | PASSED (Compliant) |
| 20.0 km | 0.204 m | 0.9980 | 19.9 DN | 100.0% | 18.09 μrad | PASSED (Compliant) |

## 3. Key Findings & Conclusions

1. **Gaussian Beam Spreading & Optical Power**:
   - Gaussian beam radius expands as $w(L) = w_0 \sqrt{1 + (L/z_R)^2}$. Over a $10\text{ cm}$ receiver aperture, captured optical power decreases with range, causing received signal amplitude to drop.
2. **Empirical Operating Envelope**:
   - For standard optical parameters ($w_0 = 5\text{ cm}$, $D_{\text{rx}} = 10\text{ cm}$, $\alpha = 0.0001\text{ km}^{-1}$), the tracker satisfies all operating envelope requirements ($P_D \ge 95\%$, $\text{RMSE}_\theta \le 100\ \mu\text{rad}$) across ranges $L \in [1.0, 10.0]\text{ km}$.
   - At $L = 20.0\text{ km}$, received signal drops below detection threshold, exceeding compliant boundaries.


Primary Objective: Investigate how beacon propagation distance ($L \in [1, 20]\text{ km}$) affects received optical power $P_{\text{received}}(L)$, Gaussian beam waist expansion $w(L)$, apparent spot size, detection probability $P_D$, and angular pointing accuracy $\text{RMSE}_\theta$, establishing the empirical operating envelope of the tracker.
Operating Envelope Requirements:
Minimum Detection Probability: $P_D \ge 95.0%$
Maximum False Alarm Rate: $P_{\text{FA}} \le 1.0%$
Maximum Angular Pointing RMSE: $\text{RMSE}_\theta \le 100.0\ \mu\text{rad}$
2. Experimental Stage Results & Operating Envelope Summary
Stage 13E: Combined Link & Operating Envelope Classification ($w_0 = 5\text{ cm}$, $D_{\text{rx}} = 10\text{ cm}$, $\lambda = 1550\text{ nm}$, $\alpha = 0.0001\text{ km}^{-1}$)
Range $L$ (km)	Beam Radius $w(L)$ (m)	Transmittance $T(L)$	Received Amplitude (DN)	Gaussian Fit $P_D$ (%)	Angular Error RMSE ($\mu\text{rad}$)	Operating Envelope Status
1.0 km	$0.051\text{ m}$	0.9999	$150.2\text{ DN}$	100.0%	$17.68\ \mu\text{rad}$	✓ PASSED (Compliant)
2.0 km	$0.054\text{ m}$	0.9998	$143.8\text{ DN}$	100.0%	$17.50\ \mu\text{rad}$	✓ PASSED (Compliant)
5.0 km	$0.070\text{ m}$	0.9995	$111.8\text{ DN}$	100.0%	$19.21\ \mu\text{rad}$	✓ PASSED (Compliant)
10.0 km	$0.111\text{ m}$	0.9990	$59.2\text{ DN}$	100.0%	$18.20\ \mu\text{rad}$	✓ PASSED (Compliant)
20.0 km	$0.204\text{ m}$	0.9980	$19.9\text{ DN}$	100.0%	$18.09\ \mu\text{rad}$	✓ PASSED (Compliant)
3. Key Findings & Conclusions
Gaussian Beam Expansion & Power Link Budget:
The Gaussian beam expands with propagation distance as $w(L) = w_0 \sqrt{1 + (L/z_R)^2}$ (Rayleigh range $z_R = 5.07\text{ km}$ for $w_0 = 5\text{ cm}$, $\lambda = 1550\text{ nm}$).
Captured optical power over a $10\text{ cm}$ receiver aperture decreases with range, causing received amplitude to decrease from $150.2\text{ DN}$ at $1\text{ km}$ down to $19.9\text{ DN}$ at $20\text{ km}$.
Tracker Operating Envelope:
The tracker satisfies all compliance requirements ($P_D \ge 95%$, $\text{RMSE}\theta \le 100\ \mu\text{rad}$) across the tested range $L \in [1.0, 20.0]\text{ km}$. Subpixel pointing precision remains extremely tight ($\text{RMSE}\theta \approx 18.0\ \mu\text{rad} \approx 3.7\text{ arcsec}$).
4. Output Artifact Directories
Results & Data: 

results/exp13_beacon_range/


raw_data.csv


summary.csv


operating_envelope.csv


report.md
Figures in 

results/exp13_beacon_range/figures/
Audit Documentation: 

experiments/exp13_beacon_range/reports/implementation_audit.md
Complete Framework Experimental Matrix (Exp 00 – Exp 16)
Exp ID	Experiment Title	Primary Metrics	Status	Artifact Directory
00	Ground-Truth Generator Validation	Transmittance, Ground-Truth Metadata	Completed	

results/exp00_validation
01	Noise Robustness	Detection Probability, False Alarms	Completed	

results/exp01_noise_robustness
04	Threshold Selection	ROC curves, $P_D$ vs $P_{\text{FA}}$	Completed	

results/exp04_threshold_selection
05	Connected-Component Filtering	Rejection ratio, area filters	Completed	

results/exp05_component_filtering
06	Classical vs AI Detection	Precision, Recall, F1 Score	Completed	

results/exp06_classical_vs_ai
07	Localization Algorithm Benchmark	Subpixel RMSE, Latency	Completed	

results/exp07_localization
08	Subpixel Position Localization	Subpixel phase grid bias	Completed	

results/exp08_subpixel_localization
09	PSF Width Sensitivity	RMSE vs Gaussian spot $\sigma$	Completed	

results/exp09_psf_width
10	PSF Mismatch Robustness	Model mismatch error	Completed	

experiments/exp10_psf_mismatch/results
11	Background and PSF Interaction	$4 \times 4 \times 4$ Factorial matrix, ANOVA	Completed	

results/exp11_background_psf_interaction
12	Atmospheric Degradation	Attenuation, Turbulence, Scattering	Completed	

results/exp12_atmospheric_degradation
13	Beacon Range & Operating Envelope	Beam waist $w(L)$, Captured Power	Completed	

results/exp13_beacon_range
14	Camera FOV / Angular Pointing Error	Arctan angle error $e_\theta$ ($\mu\text{rad}$)	Completed	

results/exp14_camera_fov_angular_error
15	Moving Beacon Tracking	Trajectories $x(t), y(t)$, $T_{\text{reacquire}}$	Completed	

results/exp15_beacon_tracking
16	Motion / Frame-Rate Boundary	$P_{\text{track}}$ %, $\omega$ vs FPS	Completed	

results/exp16_motion_framerate


## 4. Reproducibility & Artifact Output
To execute Experiment 13:
```bash
python run_experiments.py --experiment 13
```
Results saved to `results/exp13_beacon_range/` and `experiments/exp13_beacon_range/results/`
