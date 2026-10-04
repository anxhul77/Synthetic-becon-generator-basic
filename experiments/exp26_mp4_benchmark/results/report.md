# EXPERIMENT C REPORT: MP4 BENCHMARK MODE

## 1. Executive Summary & Dual Operational Modes
- **Experiment ID**: exp26_mp4_benchmark
- **Title**: MP4 Video Benchmark Mode & Offline Evaluation
- **Supported Modes**:
  1. **Live Virtual Camera Mode**: Interactive simulated frame generation.
  2. **Video Benchmark Mode**: Full-frame MP4 video processing at 30 FPS with PTZ bypass mode.
- **Ground-Truth Policy**: ZERO ground-truth access during runtime execution. Evaluation performed via offline GT script.

## 2. MP4 Video Benchmark Evaluation Table

| Operational Mode | Total Frames | Lock Retention (%) | Tracking RMSE (px) | Max Error (px) | Throughput (FPS) | PTZ Bypass | GT Policy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MP4 Video Benchmark Mode | 150 | 89.3% | 0.412 px | 1.561 px | 490.6 FPS | Enabled (Full Frame) | NO (Strict Offline Comparison) |

## 3. Key Conclusions
1. **Module Reusability**: The identical detector, tracker, and localization cascade run without modification in both Live Virtual Camera Mode and MP4 Video Benchmark Mode.
2. **Evaluator Compliance**: Supports offline GT evaluation required by external video evaluation suites.
