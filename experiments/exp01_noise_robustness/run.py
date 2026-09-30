import sys
import argparse
from experiments.exp01_noise_robustness.experiment import Exp01NoiseRobustness

def main():
    parser = argparse.ArgumentParser(description="Run Experiment 1 — Noise Robustness")
    parser.add_argument("--config", type=str, default="config/experiments.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="results", help="Base directory for results")
    args = parser.parse_args()

    exp = Exp01NoiseRobustness(config_file=args.config, results_dir=args.output)
    exp.run()

if __name__ == "__main__":
    main()
