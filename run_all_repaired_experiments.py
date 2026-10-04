import os
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from experiments.exp_psf_repaired.run_experiment import RepairedPSFBenchmark
from experiments.exp_closed_loop_repaired.run_experiment import RepairedClosedLoopBenchmark
from experiments.exp_ablation_repaired.run_experiment import RepairedFairAlgorithmAblation
from experiments.exp_uncertainty_repaired.run_experiment import RepairedUncertaintyCalibration
from experiments.exp_realtime_repaired.run_experiment import RepairedRealtimeProfiling
from experiments.exp_architecture_repaired.run_experiment import RepairedArchitectureBenchmark
from experiments.exp_monte_carlo_repaired.run_experiment import RepairedMonteCarloValidation


from validate_reports import validate_all_repaired_reports


def main():
    print("=" * 80)
    print("STARTING FULL REPAIRED EXPERIMENTAL SUITE EXECUTION")
    print("Output directory: results_repaired/")
    print("=" * 80)

    # 1. PSF Benchmark
    print("\n[1/7] Running Repaired E2E PSF Benchmark...")
    exp1 = RepairedPSFBenchmark(results_dir="results_repaired")
    exp1.run(trials_override=15)

    # 2. Closed-Loop Benchmark
    print("\n[2/7] Running Repaired Closed-Loop Benchmark...")
    exp2 = RepairedClosedLoopBenchmark(results_dir="results_repaired")
    exp2.run(trials_override=1)

    # 3. Fair Algorithm Ablation
    print("\n[3/7] Running Repaired Fair Algorithm Ablation...")
    exp3 = RepairedFairAlgorithmAblation(results_dir="results_repaired")
    exp3.run(trials_override=15)

    # 4. Uncertainty / NIS Calibration
    print("\n[4/7] Running Repaired Uncertainty & NIS Calibration Audit...")
    exp4 = RepairedUncertaintyCalibration(results_dir="results_repaired")
    exp4.run(trials_override=1)

    # 5. Real-Time Profiling
    print("\n[5/7] Running Repaired Real-Time Profiling...")
    exp5 = RepairedRealtimeProfiling(results_dir="results_repaired")
    exp5.run(trials_override=1)

    # 6. Architecture Benchmark
    print("\n[6/7] Running Repaired Architecture Benchmark...")
    exp6 = RepairedArchitectureBenchmark(results_dir="results_repaired")
    exp6.run(trials_override=1)

    # 7. Monte Carlo Validation
    print("\n[7/7] Running Repaired Monte Carlo Validation (N=1000)...")
    exp7 = RepairedMonteCarloValidation(results_dir="results_repaired")
    exp7.run(trials_override=1000)

    print("\n[8/8] Running Automated Report Consistency Validation Script...")
    valid_success = validate_all_repaired_reports("results_repaired")

    if not valid_success:
        print("\n[ERROR] REPORT CONSISTENCY VALIDATION FAILED!")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("ALL 7 REPAIRED EXPERIMENTS AND CONSISTENCY VALIDATION COMPLETED SUCCESSFULLY!")
    print("Artifacts generated in results_repaired/:")
    print("  - exp_psf/")
    print("  - exp_closed_loop/")
    print("  - exp_ablation/")
    print("  - exp_uncertainty/")
    print("  - exp_realtime/")
    print("  - exp_architecture/")
    print("  - exp_monte_carlo/")
    print("=" * 80)


if __name__ == "__main__":
    main()
