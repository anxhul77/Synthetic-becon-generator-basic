# EXPERIMENTAL VALIDATION CHECKLIST

This checklist enforces scientific rigor across all repaired experiment executions for the **Meghavyuha / SIH26169 FSOC PAT Simulator**.

---

## 1. Global Pipeline Checklist

- [x] **Audit Documented**: `experiments/audit/EXPERIMENT_AUDIT.md` created.
- [x] **Shared Metrics Module**: All experiments import from `processing/shared_metrics.py`.
- [x] **Shared Metrics Unit Tests**: `tests/test_shared_metrics.py` passing 100%.
- [x] **Original Results Preserved**: `results/` folder untouched.
- [x] **Repaired Output Folder**: All repaired outputs saved to `results_repaired/`.
- [x] **Zero Ground-Truth Leakage**: Ground-truth passed strictly to offline evaluator functions.
- [x] **No Fabricated Data**: All results computed live during execution.
- [x] **No Hardcoded Conclusions**: Reports dynamically generated from measured data arrays.
- [x] **Automated Assertions**: Impossible results (e.g. duplicate trajectory hashes, invalid NIS) trigger test failure.

---

## 2. Bug Class Specific Checklist

### Bug Class 1 — E2E PSF Benchmark (`results_repaired/exp_psf/`)
- [x] Decomposed into 4 metrics: (1) Detector ROI Error, (2) Localizer Error True, (3) Localizer Error ROI, (4) E2E Error.
- [x] Evaluates Oracle-ROI Estimator Mode vs Blind End-to-End Mode.
- [x] Controlled ROI offset sweep ($0, 2, 5, 10, 20, 40, 80\text{ px}$).
- [x] Failure taxonomy implemented (`detector_miss`, `roi_clipped`, `saturation`, `low_snr`, etc.).

### Bug Class 2 — Closed-Loop Benchmark (`results_repaired/exp_closed_loop/`)
- [x] 11 distinct motion & stress scenarios with unique trajectory signatures.
- [x] Trajectory MD5 hashes verified distinct across scenarios.
- [x] Frame-by-frame raw data saved to CSV.
- [x] Acquisition time $> 0$ unless initial frame hits; Reacquisition time $> 0$ if loss occurs.

### Bug Class 3 — Fair Algorithm Ablation (`results_repaired/exp_ablation/`)
- [x] 6 truly distinct search/controller variants evaluated on identical seeds and scenes.
- [x] Realized search coverage / path length reported alongside theoretical window area.
- [x] 95% Confidence Intervals reported for all metrics.

### Bug Class 4 — Uncertainty / NIS Calibration (`results_repaired/exp_uncertainty/`)
- [x] NIS computed via matrix solve: $\mathbf{\nu}^{\text{T}} \mathbf{S}^{-1} \mathbf{\nu}$ ($\mathbb{E}[\text{NIS}] \approx 2.0$ for calibrated 2D model).
- [x] Empirical Mahalanobis coverage evaluated at 50% (1.386), 90% (4.605), and 95% (5.991) Chi2 bounds.
- [x] Output explicit Calibration Verdict (`UNDER_DISPERSED`, `OVER_DISPERSED`, `APPROXIMATELY_CALIBRATED`).

### Bug Class 5 — Real-Time Profiling (`results_repaired/exp_realtime/`)
- [x] Throughput FPS computed as $1000 / \text{total\_loop\_latency\_ms}$.
- [x] 300+ frames evaluated with 10 warm-up frames excluded.
- [x] Mean, median, P95, and P99 latencies reported.
- [x] Verified 640x480 CPU Cascaded ROI latency ($26.47\text{ ms} \rightarrow 37.8\text{ FPS} \rightarrow \text{PASS}$).

### Bug Class 6 — Architecture Benchmark (`results_repaired/exp_architecture/`)
- [x] Evaluated over 300+ frames with warm-up exclusion.
- [x] CPU, memory, P95/P99 latency, and parallel speedup % reported.

### Bug Class 7 & 8 — Camera Geometry, Monte Carlo & Template Fixes (`results_repaired/exp_monte_carlo/`)
- [x] Camera geometry explicitly derived from FOV ($f = 9163.66\text{ px}$ for $640 \times 480$ $4^\circ \times 3^\circ$ FOV).
- [x] Resolved all template tags (`{{P_VALUE}}`, `{{COHENS_D}}`) with real calculated values.
