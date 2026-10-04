# REPAIRED REAL-TIME PROFILING REPORT

## 1. Executive Summary & Methodology
- **Experiment ID**: exp_realtime
- **Output Directory**: `results_repaired/exp_realtime/`
- **Methodology**: Evaluated over sustained frames per configuration with warm-up frames excluded.
- **Throughput Formula**: Throughput (FPS) = $1000.0 / T{\text{mean\_loop\_latency\_ms}}$.

## 2. Stage-by-Stage Latency & Throughput Table

| Resolution | Search Mode | HW Target | Sample N | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Sustained FPS | SIH Criterion |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 640x480 | Cascaded ROI | CPU | 40 | 41.05 ms | 39.8 ms | 47.93 ms | 58.9 ms | **24.4 FPS** | **PASS** |
| 640x480 | Full Frame | CPU | 40 | 85.58 ms | 83.14 ms | 105.32 ms | 131.28 ms | **11.7 FPS** | <span style='color:red'>FAIL</span> |
| 1920x1080 | Cascaded ROI | CPU | 40 | 240.89 ms | 237.46 ms | 254.74 ms | 291.86 ms | **4.2 FPS** | <span style='color:red'>FAIL</span> |
| 1920x1080 | Cascaded ROI | GPU | 40 | 107.83 ms | 107.42 ms | 112.92 ms | 127.85 ms | **9.3 FPS** | <span style='color:red'>FAIL</span> |
| 2000x2000 | Cascaded ROI | CPU | 40 | 467.05 ms | 462.2 ms | 505.35 ms | 524.92 ms | **2.1 FPS** | <span style='color:red'>FAIL</span> |
| 2000x2000 | Cascaded ROI | GPU | 40 | 210.06 ms | 209.2 ms | 226.49 ms | 229.28 ms | **4.8 FPS** | <span style='color:red'>FAIL</span> |

## 3. Scientific Conclusions
1. **SIH Throughput Compliance**: 640x480 Cascaded ROI CPU achieves **41.05 ms** (**24.4 FPS**) and passes the SIH >=20 FPS criterion by **1.22x**.
2. **Full Frame Baseline**: 640x480 Full Frame CPU achieves **85.58 ms** (**11.7 FPS**).
