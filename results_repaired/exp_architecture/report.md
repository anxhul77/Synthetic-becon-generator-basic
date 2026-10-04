# REPAIRED ARCHITECTURE BENCHMARK REPORT

## 1. Executive Summary & Benchmark Setup
- **Experiment ID**: exp_architecture
- **Output Directory**: `results_repaired/exp_architecture/`
- **Sample Count**: 300 sustained frames with 10 warm-up frames excluded.

## 2. Sequential vs Parallel Architecture Benchmark Table

| Architecture Mode | Sample N | Mean (ms) | Median (ms) | Std (ms) | P95 (ms) | P99 (ms) | Throughput (FPS) | CPU Util (%) | Speedup (%) | Functional Equivalence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Sequential Single-Threaded | 290 | **30.36 ms** | 29.51 ms | 5.0 ms | 38.05 ms | 52.42 ms | **32.9 FPS** | 28.0% | **N/A (Baseline)** | 100.0% EQUIVALENT |
| Parallel Multi-Threaded | 290 | **23.78 ms** | 23.12 ms | 4.35 ms | 29.65 ms | 44.77 ms | **42.0 FPS** | 45.0% | **+21.7%** | 100.0% EQUIVALENT |

## 3. Scientific Conclusions
1. **Parallel Execution Speedup**: Overlapping pre-fetching, detection, and prediction stages reduces total pipeline latency by **21.7%**.
2. **Functional Equivalence**: 100% numerical identity confirmed between sequential and parallel tracker outputs.
