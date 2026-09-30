# EXPERIMENT 16 — MOTION / FRAME-RATE EXPERIMENT AUDIT & SPECIFICATION

## 1. Executive Summary & Objective

In dynamic FSOC satellite laser communication links (LEO-to-ground, air-to-ground, or inter-satellite links), relative platform dynamics induce beacon angular velocities ranging from small slew rates ($\omega \approx 0.1^\circ/\text{s}$) up to rapid fast steering maneuvers ($\omega \ge 10^\circ/\text{s}$). Concurrently, tracking camera sensors operate at configurable frame rates ($f_{\text{fps}} \in \{15, 30, 60, 120\}\text{ FPS}$).

The primary objective of **Experiment 16: Motion / Frame-Rate Experiment** is to map out the operational boundary of the FSOC beacon tracker across the 2D operational parameter space of **Beacon Angular Velocity ($\omega$)** and **Camera Frame Rate ($\text{FPS}$)**.

---

## 2. Angular Velocity & Kinematic Mapping

For a camera with focal length $f$ pixels, an angular velocity $\omega$ (in degrees per second) maps to a sensor pixel velocity $v_{\text{px/s}}$:
$$\omega_{\text{rad/s}} = \omega_{\text{deg/s}} \times \left(\frac{\pi}{180}\right)$$
$$v_{\text{px/s}} = f \cdot \tan(\omega_{\text{rad/s}}) \approx f \cdot \omega_{\text{rad/s}} \quad [\text{px/s}]$$

At a camera frame rate $f_{\text{fps}}$, the inter-frame beacon displacement $\Delta s$ (in pixels per frame) is:
$$\Delta s = \frac{v_{\text{px/s}}}{f_{\text{fps}}} \approx \frac{f \cdot \omega_{\text{rad/s}}}{f_{\text{fps}}} \quad [\text{px/frame}]$$

### Operational Boundary Criterion:
If $\Delta s > R_{\text{gate}}$ (where $R_{\text{gate}}$ is the tracker ROI measurement validation gate size), the beacon moves out of the ROI search window between successive frames, causing target loss ($P_{\text{track}} \rightarrow 0$) unless search expansion or predictive Kalman filtering maintains lock.

---

## 3. Parameter Grid & Conditions

- **Focal Length**: $f = 2000\text{ px}$ ($\text{FOV}_x = 51.3^\circ$).
- **Evaluated Angular Velocities ($\omega$)**:
  - $0.1^\circ/\text{s}$ ($\Delta s = 0.29\text{ px/frame}$ at $120\text{ FPS}$)
  - $1.0^\circ/\text{s}$ ($\Delta s = 2.91\text{ px/frame}$ at $30\text{ FPS}$)
  - $5.0^\circ/\text{s}$ ($\Delta s = 14.5\text{ px/frame}$ at $30\text{ FPS}$)
  - $10.0^\circ/\text{s}$ ($\Delta s = 29.1\text{ px/frame}$ at $30\text{ FPS}$)
  - $20.0^\circ/\text{s}$ ($\Delta s = 58.2\text{ px/frame}$ at $30\text{ FPS}$)
- **Evaluated Camera Frame Rates ($\text{FPS}$)**:
  - $15\text{ FPS}$ ($T_{\text{frame}} = 66.7\text{ ms}$)
  - $30\text{ FPS}$ ($T_{\text{frame}} = 33.3\text{ ms}$)
  - $60\text{ FPS}$ ($T_{\text{frame}} = 16.7\text{ ms}$)
  - $120\text{ FPS}$ ($T_{\text{frame}} = 8.33\text{ ms}$)

---

## 4. Evaluated Metrics

1. **Track Maintenance Ratio ($P_{\text{track}}$)**: Fraction of sequence frames where beacon track lock is successfully maintained ($P_{\text{track}} = N_{\text{tracked}} / N_{\text{total}}$).
2. **RMSE Angular Pointing Error ($\text{RMSE}_\theta$)**: Root mean square pointing angle error $e_\theta$ in microradians ($\mu\text{rad}$).
3. **Reacquisition Time ($T_{\text{reacquire}}$)**: Recovery time in seconds / frames required to regain track lock following target loss or transient disruption.
