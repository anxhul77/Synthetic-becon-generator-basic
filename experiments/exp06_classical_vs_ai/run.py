import argparse
from .experiment import Exp06ClassicalVsAI

def main():
    parser = argparse.ArgumentParser(description="Experiment 6: Classical vs AI vs Hybrid Beacon Detection")
    parser.add_argument("--trials", type=int, default=None, help="Override trial count")
    parser.add_argument("--config", type=str, default="config/experiments.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="results", help="Path to output directory")
    args = parser.parse_args()

    exp = Exp06ClassicalVsAI(config_file=args.config, results_dir=args.output)
    exp.run(trials_override=args.trials)

if __name__ == "__main__":
    main()
