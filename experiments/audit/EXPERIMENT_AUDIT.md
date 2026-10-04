# EXPERIMENTAL VALIDATION PIPELINE AUDIT REPORT

**Project**: Meghavyuha / SIH26169 FSOC Coarse-PAT Simulator  
**Date**: October 4, 2026  
**Auditor**: Lead Technical Auditor & AI Coding Assistant  

---

## 1. Audit Overview & Methodology

A comprehensive code and results audit was performed across all experimental modules to identify methodological flaws, ground-truth leaks, hardcoded performance text, metric conflations, and statistical inconsistencies.

### Core Audit Principles Enforced:
1. **Zero Ground-Truth Leakage in Runtime Path**: Ground truth is passed strictly to the offline evaluator.
2. **Result Preservation**: Original `results/` directory remains untouched. Repaired results are saved exclusively to `results_repaired/`.
3. **Automated Assertions**: Impossible or duplicated results cause explicit test failure rather than silent reporting.
4. **Dynamic Report Generation**: Markdown reports derive 100% of their tables and conclusions directly from measured data arrays.

---

## 2. Detailed Bug Class Audit Findings

### Bug Class 1 — E2E PSF Benchmark
- **Current Status**: FAILED / CONFLATED.
- **Suspected Bug**: Conflation of detector ROI acquisition error, subpixel localization error, and PSF model mismatch, resulting in reported end-to-end RMSE of ~129 px with ROI offsets up to 400 px without error decomposition.
- **Evidence**: `DualBenchmarkEngine` in `processing/benchmark_evaluator.py` combined detector misses directly into localizer RMSE.
- **Affected Metrics**: Localizer RMSE, E2E RMSE, Subpixel accuracy.
- **Proposed Correction**: Re-implement benchmark with 4 decomposed error metrics:
  1. Detector ROI Error
  2. Localizer Error relative to True Target
  3. Localizer Error relative to ROI Center
  4. Total E2E Error  
  Run two distinct modes: Oracle-ROI Estimator Mode vs Blind End-to-End Mode. Perform controlled ROI offset sweep (0, 2, 5, 10, 20, 40, 80 px) and introduce explicit failure taxonomy (`detector_miss`, `roi_clipped`, `roi_outside_image`, `saturation`, `low_snr`, `psf_mismatch`, `tracker_loss`, `localization_failure`).
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_psf/`.

---

### Bug Class 2 — Closed-Loop Benchmark (Exp 25)
- **Current Status**: FAILED / METRIC REUSE.
- **Suspected Bug**: 8 different motion scenarios produced identical RMSE, max error, lock retention, target loss, command rate, and search path length.
- **Evidence**: Trajectory generator parameters were hardcoded, resulting in identical trajectory data being evaluated across different scenario labels.
- **Affected Metrics**: All 11 scenario performance columns.
- **Proposed Correction**: Re-implement each scenario with an independent, unique target trajectory signature, camera disturbance, and frame stream. Add assertions verifying MD5 trajectory hash uniqueness, non-zero acquisition/reacquisition times where applicable, and dynamic report generation.
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_closed_loop/`.

---

### Bug Class 3 — Fair Algorithm Ablation (Exp 27)
- **Current Status**: FAILED / INEFFECTIVE ABLATION.
- **Suspected Bug**: All 6 algorithm variants produced identical RMSE (0.547 px) and lock retention (91.4%), with only theoretical search area varying.
- **Evidence**: Controller/search logic in `exp27_fair_algorithm_ablation/src/run_experiment.py` did not modify the actual runtime search window or camera control sequence.
- **Affected Metrics**: Tracking RMSE, Lock Retention, Search Path Length, Realized Coverage.
- **Proposed Correction**: Re-implement 6 truly distinct search/controller variants (Fixed, Current-Position, Predictive, Covariance-Shaped, Cov+NIS Adaptation, Cov+NIS+Delayed Horizon). Measure realized coverage vs theoretical area under identical random seeds and scenes with 95% CIs.
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_ablation/`.

---

### Bug Class 4 — Uncertainty / NIS Calibration (Exp 28)
- **Current Status**: FAILED / SUSPECT CONSISTENCY CLAIM.
- **Suspected Bug**: Mean NIS was reported as ~32.71 while labeling the filter "CONSISTENT". For a 2D innovation, theoretical expected NIS is ~2.0.
- **Evidence**: NIS calculation omitted inverse covariance scaling or used un-normalized position residuals.
- **Affected Metrics**: Mean NIS, Mahalanobis Coverage (50%, 90%, 95%).
- **Proposed Correction**: Implement Cholesky-based NIS solver $\mathbf{\nu}^{\text{T}} \mathbf{S}^{-1} \mathbf{\nu}$. Compare Mahalanobis distance squared against Chi-Square df=2 thresholds (50%: 1.386, 90%: 4.605, 95%: 5.991). Output explicit calibration verdicts (`UNDER_DISPERSED`, `OVER_DISPERSED`, `APPROXIMATELY_CALIBRATED`).
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_uncertainty/`.

---

### Bug Class 5 — Real-Time Profiling (Exp 29)
- **Current Status**: REPAIRED / REPORT MISMATCH FIXED.
- **Suspected Bug**: Measured 640x480 CPU latency was 26.47 ms (37.8 FPS, valid PASS >=20 FPS), but report text claimed <15 ms / >65 FPS.
- **Evidence**: Hardcoded text snippet in markdown builder contradicted summary CSV.
- **Affected Metrics**: Report narrative text.
- **Proposed Correction**: Derive FPS strictly from `1000 / total_loop_latency_ms`. Automatically generate all report text from measured data arrays with warm-up exclusion over 300+ frames.
- **Retain Original Result**: Retain raw data, re-build report in `results_repaired/exp_realtime/`.

---

### Bug Class 6 — Exp 23 Architecture Benchmark
- **Current Status**: FAILED / INSUFFICIENT SAMPLE SIZE.
- **Suspected Bug**: Evaluated over only N=5 frames.
- **Evidence**: High sample variance; un-sustained throughput estimates.
- **Affected Metrics**: Mean, median, P95, P99 latency, parallel speedup.
- **Proposed Correction**: Re-run over 300+ sustained frames with 10 warm-up frames excluded. Measure CPU, memory, P95, P99 latencies, and speedup %.
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_architecture/`.

---

### Bug Class 7 & 8 — Camera Geometry, Monte Carlo & Template Placeholders
- **Current Status**: FAILED / UNRESOLVED TEMPLATE VARIABLES.
- **Suspected Bug**: Reports contained unresolved placeholders `{{P_VALUE}}`, `{{COHENS_D}}`, `{{STATISTIC}}`. Camera focal length `fx=2000` on 1920x1080 was mixed with 4° FOV specs.
- **Evidence**: Unfilled markdown template tags in output files.
- **Affected Metrics**: Statistical significance metrics, camera geometry descriptions.
- **Proposed Correction**: Calculate exact p-values, Cohen's d, and statistics dynamically. Derive focal lengths explicitly from FOV ($f_x = \frac{W/2}{\tan(\text{FOV}_x/2)}$).
- **Retain Original Result**: No. Must be re-run into `results_repaired/exp_monte_carlo/`.

---

## 3. Summary of Repaired Output Directories

| Bug Class | Experiment | Repaired Directory Path | Primary Fix |
| :--- | :--- | :--- | :--- |
| **Bug Class 1** | E2E PSF Benchmark | `results_repaired/exp_psf/` | 4-metric decomposition, Oracle vs Blind modes, ROI-offset sweep |
| **Bug Class 2** | Closed-Loop Benchmark | `results_repaired/exp_closed_loop/` | 11 unique trajectories, frame-by-frame CSVs, GT leakage assertions |
| **Bug Class 3** | Fair Algorithm Ablation | `results_repaired/exp_ablation/` | 6 truly distinct search variants, realized vs theoretical area, 95% CIs |
| **Bug Class 4** | Uncertainty / NIS Audit | `results_repaired/exp_uncertainty/` | Cholesky NIS solver, Chi2 df=2 coverage (50, 90, 95%), Calibration Verdict |
| **Bug Class 5** | Real-Time Profiling | `results_repaired/exp_realtime/` | Dynamic report derivation, 300+ frames, P95/P99 latency |
| **Bug Class 6** | Architecture Benchmark | `results_repaired/exp_architecture/` | 300+ frames, warm-up exclusion, CPU/memory profiling |
| **Bug Class 7/8** | Monte Carlo & Geometry | `results_repaired/exp_monte_carlo/` | Fixed camera geometry ($f=9163.66\text{ px}$), resolved template tags |
