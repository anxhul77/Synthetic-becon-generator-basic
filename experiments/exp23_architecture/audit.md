# Dependency Audit for Experiment 23 — Sequential vs. Parallel Processing Architecture

## 1. Overview
This dependency audit assesses the availability, reusability, and required modifications for existing repository components to support **Experiment 23: Sequential vs. Parallel Processing Architecture for FSOC Beacon Detection**.

---

## 2. Component Audit Table

| Component | Existing Implementation | Reusable | Required Modification |
| :--- | :--- | :---: | :--- |
| **Frame Generator** | `generator/generator.py` (`SyntheticBeaconGenerator`), `generator/camera.py` (`PinholeCamera`) | **Yes** | None. Reused directly for generating identical 1080p synthetic beacon frames across SNR levels and backgrounds. |
| **Classical Detector** | `processing/detector.py` (`ClassicalBeaconDetector`), `processing/component_filtering.py` (`get_component_filter`) | **Yes** | None. Uses thresholding ($T_g = 160.0$) with connected-component filtering. |
| **AI Detector** | `experiments/exp06_classical_vs_ai/ai_detector.py` (`AIBeaconDetector`), checkpoint `results/exp06_classical_vs_ai/models/exp06_beacon_ai_model.pt` | **Yes** | Wrap inference cleanly to allow thread-safe execution during parallel dispatch. |
| **Fusion Algorithm** | `experiments/exp06_classical_vs_ai/hybrid_detector.py` (`HybridBeaconDetector`) | **Yes** | Ensure deterministic ordering of candidates regardless of asynchronous completion order. |
| **Localization Algorithm** | `processing/localization.py` (`intensity_weighted_centroid`) | **Yes** | None. Intensity-weighted subpixel centroiding applied to candidate ROI. |
| **Benchmark Runner** | `run_experiments.py` | **Yes** | Add `exp23_architecture` CLI option and lazy registration module. |
| **Test Suite** | `pytest` framework under `tests/` | **Yes** | Add `tests/test_exp23.py` for sequential, parallel, functional equivalence, and benchmark metric tests. |

---

## 3. Dependency Verification Status
- **Trained AI Model Weights**: Verified at `results/exp06_classical_vs_ai/models/exp06_beacon_ai_model.pt` (200.7 KB, 35,425 parameters).
- **Classical Filter Registry**: Verified at `processing/component_filtering.py`.
- **Concurrency Support**: Native Python `concurrent.futures.ThreadPoolExecutor` and `ProcessPoolExecutor` available.
- **Hardware Constraints**: CPU multi-threading (Intel/AMD x86_64, Windows environment). PyTorch CPU threads set to match available logical cores (`os.cpu_count()`).

---

## 4. Hardware & Software Environment
- **CPU**: Windows x86_64 Multi-core CPU
- **Python**: Python 3.11+
- **PyTorch**: 2.x CPU PyTorch build
- **Timing Instrumentation**: `time.perf_counter()` high-resolution monotonic timer.
