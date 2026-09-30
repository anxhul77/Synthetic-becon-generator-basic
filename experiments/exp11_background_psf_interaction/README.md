# Experiment 11: Background and PSF Interaction

## Overview
This experiment investigates how optical spot width ($\sigma \in \{1.0, 2.0, 3.0, 4.0\}$ px), background conditions ($B \in \{10, 50, 100, 200\}$ DN; uniform and gradient types), and signal-to-noise ratio ($\text{SNR} \in \{5, 10, 15, 20\}$ dB) jointly interact to influence subpixel beacon localization accuracy, systematic bias, fitting convergence, and processing latency.

## Directory Structure
```text
experiments/
└── exp11_background_psf_interaction/
    ├── audit.md
    ├── config.yaml
    ├── README.md
    ├── src/
    │   ├── __init__.py
    │   ├── factorial_analysis.py
    │   ├── plotting.py
    │   └── run_experiment.py
    └── results/
        ├── raw_data.csv
        ├── summary.csv
        ├── paired_comparison.csv
        ├── interaction_analysis.csv
        ├── factorial_model.csv
        ├── failures.csv
        ├── config.yaml
        ├── report.md
        └── figures/
            ├── psf_snr_rmse_heatmaps.png
            ├── psf_background_rmse_heatmaps.png
            ├── psf_snr_interaction.png
            ├── psf_background_interaction.png
            ├── snr_background_interaction.png
            ├── localization_bias.png
            ├── success_rate_heatmaps.png
            ├── runtime_comparison.png
            ├── angular_rmse_heatmaps.png
            └── error_distributions.png
```

## How to Run
```bash
python run_experiments.py --experiment 11
```
Or for custom trial counts:
```bash
python run_experiments.py --experiment 11 --trials 50
```
