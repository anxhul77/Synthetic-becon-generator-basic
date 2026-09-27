import argparse
import sys
import os

from experiments.exp00_validation import Exp00Validation

def main():
    parser = argparse.ArgumentParser(description="FSOC Beacon Tracking Experimental Framework")
    parser.add_argument("--experiment", type=str, default="00", help="Experiment ID to run (e.g. 00, 01, ..., 18, or 'all')")
    parser.add_argument("--trials", type=int, default=None, help="Override number of trials")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--config", type=str, default="config/experiments.yaml", help="Path to experiment config file")
    parser.add_argument("--output", type=str, default="results", help="Path to output results directory")

    args = parser.parse_args()

    exp_id = args.experiment.strip().lower()
    if exp_id in ["00", "exp00", "0"]:
        print("\n====================================================")
        print("RUNNING EXPERIMENT 00: GROUND-TRUTH GENERATOR VALIDATION")
        print("====================================================\n")
        exp = Exp00Validation(config_file=args.config)
        exp.results_dir = args.output
        df, report = exp.run()
        print("\n====================================================")
        print("EXPERIMENT 00 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    else:
        print(f"Experiment '{args.experiment}' requested.")
        print("Note: Currently only Experiment 00 is executed as instructed by user prompt.")

if __name__ == "__main__":
    main()
