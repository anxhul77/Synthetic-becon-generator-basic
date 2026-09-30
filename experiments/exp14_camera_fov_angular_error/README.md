# Experiment 14: Camera FOV and Angular Pointing Error Analysis

## Overview
This experiment formulates and evaluates physical angular pointing error $e_\theta$ (in microradians $\mu\text{rad}$) as a function of camera focal length ($f_x, f_y \in \{500, 1000, 2000, 4000, 8000\}$ px), sensor Field of View ($\text{FOV}_x^\circ$), off-axis sensor radial field position, and signal-to-noise ratio.

## Directory Structure
```text
experiments/
└── exp14_camera_fov_angular_error/
    ├── audit.md
    ├── config.yaml
    ├── README.md
    ├── src/
    │   ├── __init__.py
    │   ├── angular_evaluation.py
    │   ├── plotting.py
    │   └── run_experiment.py
    └── results/
        ├── raw_data.csv
        ├── summary.csv
        ├── fov_angular_summary.csv
        ├── paired_comparison.csv
        ├── failures.csv
        ├── config.yaml
        ├── report.md
        └── figures/
            ├── angular_rmse_vs_focal_length.png
            ├── pixel_vs_angular_error_comparison.png
            ├── fov_vs_angular_precision.png
            ├── off_axis_angular_error.png
            ├── angular_error_heatmaps.png
            ├── angular_bias_analysis.png
            ├── angular_error_distributions.png
            ├── angular_precision_gain.png
            ├── estimator_angular_comparison.png
            └── runtime_vs_focal_length.png
```

## How to Run
```bash
python run_experiments.py --experiment 14
```
Or for custom trial counts:
```bash
python run_experiments.py --experiment 14 --trials 50
```
