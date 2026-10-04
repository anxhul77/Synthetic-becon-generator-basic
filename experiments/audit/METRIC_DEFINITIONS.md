# SHARED METRICS DEFINITIONS & MATHEMATICAL FORMULAS

This document specifies the standard, shared metrics definitions for the **Meghavyuha / SIH26169 FSOC PAT Simulator**. All experiments MUST import from `processing/shared_metrics.py`.

---

## 1. Decomposed Position & Localization Errors

To eliminate conflation between detector acquisition error and subpixel localization error, errors are decomposed into four explicit metrics:

1. **Detector ROI Acquisition Error ($e_{\text{ROI}}$ in px)**:
   $$e_{\text{ROI}} = \|\mathbf{c}_{\text{ROI}} - \mathbf{x}_{\text{true}}\| = \sqrt{(c_x - x_{\text{true}})^2 + (c_y - y_{\text{true}})^2}$$

2. **Localizer Error Relative to True Target ($e_{\text{loc,true}}$ in px)**:
   $$e_{\text{loc,true}} = \|\hat{\mathbf{x}} - \mathbf{x}_{\text{true}}\| = \sqrt{(\hat{x} - x_{\text{true}})^2 + (\hat{y} - y_{\text{true}})^2}$$

3. **Localizer Error Relative to ROI Center ($e_{\text{loc,ROI}}$ in px)**:
   $$e_{\text{loc,ROI}} = \|\hat{\mathbf{x}} - \mathbf{c}_{\text{ROI}} - \mathbf{\Delta x}_{\text{local\_gt}}\|$$

4. **Total End-to-End Tracking Error ($e_{\text{E2E}}$ in px)**:
   $$e_{\text{E2E}} = \|\hat{\mathbf{x}} - \mathbf{x}_{\text{true}}\|$$

---

## 2. Statistical Aggregations & Confidence Bounds

For any metric sample $X = \{x_1, x_2, \dots, x_N\}$:

- **Root Mean Square Error ($\text{RMSE}$)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N x_i^2}$$

- **Sample Standard Deviation ($s$)**:
  $$s = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (x_i - \bar{x})^2}$$

- **95% Confidence Interval Error Bound ($\text{CI}_{95}$)**:
  $$\text{CI}_{95} = z_{0.975} \cdot \frac{s}{\sqrt{N}} \approx 1.96 \cdot \frac{s}{\sqrt{N}}$$

---

## 3. Closed-Loop Tracking Performance Metrics

- **Acquisition Time ($T_{\text{acq}}$ in seconds)**:
  First time $t_k = k \cdot \Delta t$ where the tracking validation criterion ($d_{\text{error}} \le R_{\text{gate}}$) is continuously satisfied for $N_{\text{lock}} = 2$ consecutive frames.

- **Lock Retention Percentage ($P_{\text{lock}}$ in %)**:
  $$P_{\text{lock}} = \frac{N_{\text{tracked}}}{N_{\text{eligible}}} \times 100\%$$

- **Target Loss Percentage ($P_{\text{loss}}$ in %)**:
  $$P_{\text{loss}} = \frac{N_{\text{loss}}}{N_{\text{eligible}}} \times 100\%$$

- **Reacquisition Time ($T_{\text{reacq}}$ in ms)**:
  Average duration (ms) from a confirmed track loss until the tracking validation criterion is satisfied again for $N_{\text{lock}} = 2$ consecutive frames.

---

## 4. Kalman Innovation & NIS Statistics

- **Normalized Innovation Squared ($\text{NIS}$)**:
  $$\mathbf{\nu}_k = \mathbf{z}_k - \mathbf{H} \hat{\mathbf{x}}_{k|k-1}$$
  $$\mathbf{S}_k = \mathbf{H} \mathbf{P}_{k|k-1} \mathbf{H}^{\text{T}} + \mathbf{R}_k$$
  $$\text{NIS}_k = \mathbf{\nu}_k^{\text{T}} \mathbf{S}_k^{-1} \mathbf{\nu}_k$$
  *(Computed via Cholesky decomposition $\mathbf{S}_k = \mathbf{L} \mathbf{L}^{\text{T}}$)*

- **Theoretical Chi-Square Bounds ($\chi^2_2$)**:
  - 50% Mahalanobis Gate: $\chi^2_{2, 0.50} = 1.3863$
  - 90% Mahalanobis Gate: $\chi^2_{2, 0.90} = 4.6052$
  - 95% Mahalanobis Gate: $\chi^2_{2, 0.95} = 5.9915$

- **Calibration Verdict**:
  - `UNDER_DISPERSED`: $\mathbb{E}[\text{NIS}] > 4.0$ or $P_{95\%} < 85\%$
  - `OVER_DISPERSED`: $\mathbb{E}[\text{NIS}] < 0.8$ or $P_{50\%} > 75\%$
  - `APPROXIMATELY_CALIBRATED`: $0.8 \le \mathbb{E}[\text{NIS}] \le 4.0$ and $85\% \le P_{95\%} \le 98\%$

---

## 5. Real-Time Profiling & Throughput

- **End-to-End Loop Throughput ($\text{FPS}$)**:
  $$\text{FPS} = \frac{1000.0}{T_{\text{total\_loop\_latency\_ms}}}$$
  *(Measured over sustained execution after excluding the first 10 warm-up frames).*
