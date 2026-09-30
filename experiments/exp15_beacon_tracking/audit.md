# EXPERIMENT 15 — MOVING BEACON TRACKING AUDIT & SPECIFICATION

## 1. Executive Summary & Objective

In prior experiments (Exp 00–14), localization performance was evaluated on isolated single static frames. In an operational Free-Space Optical Communication (FSOC) system, the terminal optics, fine steering mirrors (FSM), and coarse gimbal assemblies track a dynamic moving beacon across consecutive image frames $t = 1, 2, \dots, N$.

The objective of **Experiment 15: Beacon Tracking** is to extend the single-frame subpixel beacon localization engine into a full-sequence temporal beacon tracking pipeline. The system evaluates tracking performance across controlled target motion models, quantifying:
1. **Temporal Position Error**: $e(t) = \sqrt{(\hat{x}(t) - x(t))^2 + (\hat{y}(t) - y(t))^2}$ [pixels]
2. **Angular Pointing Error**: $e_\theta(t) = \sqrt{(\hat{\theta}_x(t) - \theta_x(t))^2 + (\hat{\theta}_y(t) - \theta_y(t))^2}$ [microradians]
3. **Tracking Loss Count & Ratio**: Number and percentage of frames where the beacon target is lost ($e(t) > R_{\text{gate}}$ or detection failure).
4. **Reacquisition Time**: $T_{\text{reacquire}}$ [frames or seconds], defined as the temporal duration required for the tracker to transition from `LOST` state back to `TRACKING` state following a temporary occlusion, severe disturbance, or signal loss.
5. **Frame Processing Latency**: $T_{\text{processing}}$ [milliseconds per frame].

---

## 2. Dynamic Motion Models

The synthetic sequence generator produces continuous 2D motion trajectories $(x(t), y(t))$ over $N$ frames sampled at frame rate $f_{\text{fps}}$ ($t_k = k / f_{\text{fps}}$):

### Model 1: Constant Velocity (CV)
Linear uniform motion:
$$x(t) = x_0 + v_x \cdot t$$
$$y(t) = y_0 + v_y \cdot t$$

### Model 2: Accelerating Motion (CA)
Motion with constant acceleration vector $(a_x, a_y)$:
$$x(t) = x_0 + v_{x,0} \cdot t + \frac{1}{2} a_x t^2$$
$$y(t) = y_0 + v_{y,0} \cdot t + \frac{1}{2} a_y t^2$$

### Model 3: Sinusoidal Motion (Lissajous / Vibration)
Simulates high-frequency angular jitter or atmospheric/platform vibration:
$$x(t) = x_0 + A_x \sin(\omega_x t + \phi_x)$$
$$y(t) = y_0 + A_y \cos(\omega_y t + \phi_y)$$

### Model 4: Random Maneuver (Gauss-Markov Acceleration / Random Walk)
Piecewise acceleration changes at discrete time intervals, modeling unpredictable platform maneuvers or satellite thruster firings:
$$\mathbf{a}_k = \rho \mathbf{a}_{k-1} + \mathbf{w}_k, \quad \mathbf{w}_k \sim \mathcal{N}(\mathbf{0}, \sigma_a^2 \mathbf{I})$$

### Model 5: Temporary Occlusion / Cloud Fade Scenario
The beacon trajectory proceeds normally, but during a controlled time window $t \in [t_{\text{start}}, t_{\text{end}}]$, the beacon amplitude drops to zero ($A(t) = 0$) or drops below the noise floor, testing tracker prediction, loss detection, search expansion, and reacquisition ($T_{\text{reacquire}}$).

---

## 3. Tracker Architecture & State Machine

The FSOC sequence tracker operates a Kalman Filter predictor combined with dynamic Gated ROI Cropping:

### State Vector & Prediction
$$\mathbf{x}_k = \begin{bmatrix} x_k & y_k & \dot{x}_k & \dot{y}_k \end{bmatrix}^T$$
$$\mathbf{x}_{k|k-1} = \mathbf{F} \mathbf{x}_{k-1|k-1}, \quad \mathbf{P}_{k|k-1} = \mathbf{F} \mathbf{P}_{k-1|k-1} \mathbf{F}^T + \mathbf{Q}$$

### Dynamic ROI Extraction
The measurement ROI of size $W_{\text{roi}} \times W_{\text{roi}}$ is centered at predicted position $(\hat{x}_{k|k-1}, \hat{y}_{k|k-1})$.

### Measurement & Correction
Subpixel localization (Gaussian Fitting / Centroid) yields measurement $\mathbf{z}_k = [\tilde{x}_k, \tilde{y}_k]^T$.
Residual innovation $\mathbf{y}_k = \mathbf{z}_k - \mathbf{H} \mathbf{x}_{k|k-1}$.
Validation gate check: $\mathbf{y}_k^T \mathbf{S}_k^{-1} \mathbf{y}_k \le \gamma^2$.
If valid: update state $\mathbf{x}_{k|k}$, set state to `TRACKING`.
If invalid/missing: update state using motion prediction only, increment loss counter, transition state (`TRACKING` $\rightarrow$ `LOST`).

---

## 4. Evaluation Metrics

1. **RMSE Position Error**: $\text{RMSE}_p = \sqrt{\frac{1}{N_{\text{valid}}} \sum_{k \in \text{valid}} e(t_k)^2}$
2. **RMSE Pointing Error**: $\text{RMSE}_\theta = \sqrt{\frac{1}{N_{\text{valid}}} \sum_{k \in \text{valid}} e_\theta(t_k)^2}$ [$\mu\text{rad}$]
3. **Track Maintenance Ratio ($P_{\text{track}}$)**: $N_{\text{tracked}} / N_{\text{total}}$
4. **Reacquisition Time ($T_{\text{reacquire}}$)**: Frames elapsed from beacon reappearance ($t_{\text{end}}$) until first valid gate match.
5. **Processing Latency ($T_{\text{processing}}$)**: Execution time per frame in milliseconds.
