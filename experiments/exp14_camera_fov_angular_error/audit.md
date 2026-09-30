# EXPERIMENT 14 AUDIT — CAMERA FOV AND ANGULAR POINTING ERROR

## 1. Audit Overview & Scientific Objective
This audit verifies codebase compatibility, component reuse, and architectural design for **Experiment 14: Camera FOV and Angular Pointing Error Analysis**.
In Free-Space Optical Communication (FSOC) optical tracking testbeds, pointing accuracy is evaluated in physical angular space ($\text{rad}, \mu\text{rad}$) rather than sensor pixels.
The objective of Experiment 14 is to formulate and evaluate exact pointing angle errors ($e_\theta$) across camera focal lengths ($f_x, f_y \in \{500, 1000, 2000, 4000, 8000\}$ px), corresponding Fields-Of-View ($\text{FOV}_x \in [13.6^\circ, 125.0^\circ]$), sensor radial field offsets ($R \in \{0, 200, 400, 600, 800\}$ px), and SNR levels.

---

## 2. Mathematical Formulation & Angular Metrics

### 2.1 Pinhole Arctan Projection Model
For camera focal lengths $f_x, f_y$ and principal point $(c_x, c_y) = (960.0, 540.0)$ px:

1. **Ground-Truth Beacon Angle**:
   $$\theta_{x,\text{true}} = \tan^{-1}\left(\frac{x_{\text{true}} - c_x}{f_x}\right), \quad \theta_{y,\text{true}} = \tan^{-1}\left(\frac{y_{\text{true}} - c_y}{f_y}\right)$$

2. **Estimated Beacon Angle**:
   $$\hat{\theta}_x = \tan^{-1}\left(\frac{\hat{x} - c_x}{f_x}\right), \quad \hat{\theta}_y = \tan^{-1}\left(\frac{\hat{y} - c_y}{f_y}\right)$$

3. **Angular Pointing Errors**:
   $$e_{\theta,x} = \hat{\theta}_x - \theta_{x,\text{true}}, \quad e_{\theta,y} = \hat{\theta}_y - \theta_{y,\text{true}}$$
   $$e_\theta = \sqrt{e_{\theta,x}^2 + e_{\theta,y}^2} \quad [\text{radians}]$$
   $$e_{\theta,\mu\text{rad}} = e_\theta \times 10^6 \quad [\text{microradians } \mu\text{rad}]$$

4. **Camera Field of View (FOV)**:
   $$\text{FOV}_x = 2 \tan^{-1}\left(\frac{W}{2 f_x}\right), \quad \text{FOV}_y = 2 \tan^{-1}\left(\frac{H}{2 f_y}\right)$$

5. **Paraxial Angular Scale ($\mu\text{rad}/\text{px}$)**:
   $$S_{\text{center}} = \frac{10^6}{f_x} \quad [\mu\text{rad} / \text{pixel}]$$
   - $f_x = 500\text{ px} \implies S_{\text{center}} = 2000.0\ \mu\text{rad/px}$
   - $f_x = 1000\text{ px} \implies S_{\text{center}} = 1000.0\ \mu\text{rad/px}$
   - $f_x = 2000\text{ px} \implies S_{\text{center}} = 500.0\ \mu\text{rad/px}$
   - $f_x = 4000\text{ px} \implies S_{\text{center}} = 250.0\ \mu\text{rad/px}$
   - $f_x = 8000\text{ px} \implies S_{\text{center}} = 125.0\ \mu\text{rad/px}$

---

## 3. Codebase Component Reuse

| Component / Utility | File Path | Reuse Purpose | Status |
| :--- | :--- | :--- | :---: |
| **Camera Pinhole Model** | `generator/camera.py` | `PinholeCamera` class for intrinsic projections & pixel-to-angle mapping | Verified |
| **Synthetic Frame Generator** | `generator/generator.py` | `SyntheticBeaconGenerator` for physical rendering pipeline | Verified |
| **ROI Extractor** | `experiments/exp07_localization/src/roi_extractor.py` | `ROIExtractor` for ground-truth centered $31\times31$ px crop | Verified |
| **Estimator Implementations** | `experiments/exp07_localization/src/` | `IntensityWeightedCentroid`, `GaussianFitting`, `PSFAwareFitting` | Verified |
| **Angular Evaluation Engine** | `experiments/exp07_localization/src/localization_evaluation.py` | `compute_pixel_and_angular_errors` exact pinhole transformation | Verified |
| **Base Experiment Pipeline** | `experiments/base_experiment.py` | `BaseExperiment` for reproducibility, bootstrapping, and reporting | Verified |

---

## 4. Audit Conclusions
The codebase natively supports exact non-linear pinhole arctan projections and microradian angular metrics. No structural modifications to the physical image generator are required; Experiment 14 will sweep focal length optics and field position parameters to evaluate pointing angle precision ($e_\theta$).
