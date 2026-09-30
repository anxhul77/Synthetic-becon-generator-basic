import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="FSOC Beacon Tracking Experimental Framework")
    parser.add_argument("--experiment", type=str, default="18", help="Experiment ID to run")
    parser.add_argument("--trials", type=int, default=None, help="Override number of trials per condition")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--config", type=str, default="config/experiments.yaml", help="Path to experiment config file")
    parser.add_argument("--output", type=str, default="results", help="Path to output results directory")

    args = parser.parse_args()

    exp_id = args.experiment.strip().lower()
    if exp_id in ["00", "exp00", "0"]:
        from experiments.exp00_validation import Exp00Validation
        print("\n====================================================")
        print("RUNNING EXPERIMENT 00: GROUND-TRUTH GENERATOR VALIDATION")
        print("====================================================\n")
        exp = Exp00Validation(config_file=args.config)
        exp.results_dir = args.output
        df, report = exp.run()
        print("\n====================================================")
        print("EXPERIMENT 00 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["01", "exp01", "exp01_noise_robustness", "1"]:
        from experiments.exp01_noise_robustness import Exp01NoiseRobustness
        print("\n====================================================")
        print("RUNNING EXPERIMENT 01: NOISE ROBUSTNESS")
        print("====================================================\n")
        exp = Exp01NoiseRobustness(config_file=args.config, results_dir=args.output)
        df_summary, report = exp.run()
        print("\n====================================================")
        print("EXPERIMENT 01 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["04", "exp04", "exp04_threshold_selection", "4"]:
        from experiments.exp04_threshold_selection import Exp04ThresholdSelection
        print("\n====================================================")
        print("RUNNING EXPERIMENT 04: THRESHOLD SELECTION")
        print("====================================================\n")
        exp = Exp04ThresholdSelection(config_file=args.config, results_dir=args.output)
        df_summary, df_paired, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 04 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["05", "exp05", "exp05_component_filtering", "5"]:
        from experiments.exp05_component_filtering import Exp05ComponentFiltering
        print("\n====================================================")
        print("RUNNING EXPERIMENT 05: CONNECTED-COMPONENT FILTERING")
        print("====================================================\n")
        exp = Exp05ComponentFiltering(config_file=args.config, results_dir=args.output)
        res = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 05 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["06", "exp06", "exp06_classical_vs_ai", "6"]:
        from experiments.exp06_classical_vs_ai import Exp06ClassicalVsAI
        print("\n====================================================")
        print("RUNNING EXPERIMENT 06: CLASSICAL VS AI VS HYBRID DETECTION")
        print("====================================================\n")
        exp = Exp06ClassicalVsAI(config_file=args.config, results_dir=args.output)
        res = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 06 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["07", "exp07", "exp07_localization", "7"]:
        from experiments.exp07_localization import Exp07Localization
        print("\n====================================================")
        print("RUNNING EXPERIMENT 07: COMPARISON OF BEACON LOCALIZATION ALGORITHMS")
        print("====================================================\n")
        exp = Exp07Localization(config_file=args.config, results_dir=args.output)
        df_summary, df_paired, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 07 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["08", "exp08", "exp08_subpixel_localization", "8"]:
        from experiments.exp08_subpixel_localization import Exp08SubpixelLocalization
        print("\n====================================================")
        print("RUNNING EXPERIMENT 08: SUBPIXEL POSITION LOCALIZATION ACCURACY")
        print("====================================================\n")
        exp = Exp08SubpixelLocalization(config_file=args.config, results_dir=args.output)
        df_summary, df_phase, df_paired, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 08 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["09", "exp09", "exp09_psf_width", "9"]:
        from experiments.exp09_psf_width import Exp09PSFWidth
        print("\n====================================================")
        print("RUNNING EXPERIMENT 09: PSF WIDTH AND LOCALIZATION ACCURACY")
        print("====================================================\n")
        exp = Exp09PSFWidth(config_file=args.config, results_dir=args.output)
        df_summary, df_phase, df_paired, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 09 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["10", "exp10", "exp10_psf_mismatch", "10"]:
        from experiments.exp10_psf_mismatch import Exp10PSFMismatch
        print("\n====================================================")
        print("RUNNING EXPERIMENT 10: PSF MISMATCH AND LOCALIZATION ROBUSTNESS")
        print("====================================================\n")
        exp = Exp10PSFMismatch(config_file=args.config, results_dir=args.output)
        df_summary, df_phase, df_paired, df_mismatch, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 10 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["11", "exp11", "exp11_background_psf_interaction", "11"]:
        from experiments.exp11_background_psf_interaction import Exp11BackgroundPSFInteraction
        print("\n====================================================")
        print("RUNNING EXPERIMENT 11: BACKGROUND AND PSF INTERACTION")
        print("====================================================\n")
        exp = Exp11BackgroundPSFInteraction(config_file=args.config, results_dir=args.output)
        df_summary, df_interaction, df_factorial, df_paired, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 11 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["12", "exp12", "exp12_atmospheric_degradation", "12"]:
        from experiments.exp12_atmospheric_degradation import Exp12AtmosphericDegradation
        print("\n====================================================")
        print("RUNNING EXPERIMENT 12: ATMOSPHERIC DEGRADATION EXPERIMENT")
        print("====================================================\n")
        exp = Exp12AtmosphericDegradation(config_file=args.config, results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 12 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["13", "exp13", "exp13_beacon_range", "13"]:
        from experiments.exp13_beacon_range import Exp13BeaconRange
        print("\n====================================================")
        print("RUNNING EXPERIMENT 13: BEACON RANGE AND OPERATING ENVELOPE EXPERIMENT")
        print("====================================================\n")
        exp = Exp13BeaconRange(config_file=args.config, results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 13 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["14", "exp14", "exp14_camera_fov_angular_error", "14"]:
        from experiments.exp14_camera_fov_angular_error import Exp14CameraFOVAngularError
        print("\n====================================================")
        print("RUNNING EXPERIMENT 14: CAMERA FOV / ANGULAR POINTING ERROR ANALYSIS")
        print("====================================================\n")
        exp = Exp14CameraFOVAngularError(config_file=args.config, results_dir=args.output)
        df_summary, df_fov_summary, df_paired, df_raw, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 14 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["15", "exp15", "exp15_beacon_tracking", "15"]:
        from experiments.exp15_beacon_tracking import Exp15BeaconTracking
        print("\n====================================================")
        print("RUNNING EXPERIMENT 15: MOVING BEACON TRACKING EXPERIMENT")
        print("====================================================\n")
        exp = Exp15BeaconTracking(config_file=args.config, results_dir=args.output)
        df_frames, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 15 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["16", "exp16", "exp16_motion_framerate", "16"]:
        from experiments.exp16_motion_framerate import Exp16MotionFramerate
        print("\n====================================================")
        print("RUNNING EXPERIMENT 16: MOTION AND FRAME-RATE OPERATIONAL BOUNDARY EXPERIMENT")
        print("====================================================\n")
        exp = Exp16MotionFramerate(config_file=args.config, results_dir=args.output)
        df_frames, df_grid, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 16 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["17", "exp17", "exp17_prediction_horizon_characterization", "17"]:
        from experiments.exp17_prediction_horizon_characterization import Exp17PredictionHorizonCharacterization
        print("\n====================================================")
        print("RUNNING EXPERIMENT 17: PREDICTION HORIZON CHARACTERIZATION")
        print("====================================================\n")
        exp = Exp17PredictionHorizonCharacterization(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 17 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["18", "exp18", "exp18_uncertainty_ellipse_coverage", "18"]:
        from experiments.exp18_uncertainty_ellipse_coverage import Exp18UncertaintyEllipseCoverage
        print("\n====================================================")
        print("RUNNING EXPERIMENT 18: UNCERTAINTY ELLIPSE COVERAGE")
        print("====================================================\n")
        exp = Exp18UncertaintyEllipseCoverage(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 18 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["19", "exp19", "exp19_fixed_vs_adaptive_eal", "19"]:
        from experiments.exp19_fixed_vs_adaptive_eal import Exp19FixedVsAdaptiveEAL
        print("\n====================================================")
        print("RUNNING EXPERIMENT 19: FIXED VS UNCERTAINTY-ADAPTIVE EAL")
        print("====================================================\n")
        exp = Exp19FixedVsAdaptiveEAL(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 19 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["20", "exp20", "exp20_prediction_error_adaptation", "20"]:
        from experiments.exp20_prediction_error_adaptation import Exp20PredictionErrorAdaptation
        print("\n====================================================")
        print("RUNNING EXPERIMENT 20: PREDICTION-ERROR ADAPTATION")
        print("====================================================\n")
        exp = Exp20PredictionErrorAdaptation(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 20 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["21", "exp21", "exp21_ablation_study", "21"]:
        from experiments.exp21_ablation_study import Exp21AblationStudy
        print("\n====================================================")
        print("RUNNING EXPERIMENT 21: ABLATION STUDY")
        print("====================================================\n")
        exp = Exp21AblationStudy(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 21 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["22", "exp22", "exp22_monte_carlo_validation", "22"]:
        from experiments.exp22_monte_carlo_validation import Exp22MonteCarloValidation
        print("\n====================================================")
        print("RUNNING EXPERIMENT 22: MONTE CARLO STATISTICAL VALIDATION")
        print("====================================================\n")
        exp = Exp22MonteCarloValidation(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 22 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    elif exp_id in ["23", "exp23", "exp23_architecture", "23"]:
        from experiments.exp23_architecture import Exp23ArchitectureBenchmark
        print("\n====================================================")
        print("RUNNING EXPERIMENT 23: SEQUENTIAL VS PARALLEL ARCHITECTURE BENCHMARK")
        print("====================================================\n")
        exp = Exp23ArchitectureBenchmark(results_dir=args.output)
        df_raw, df_summary, report = exp.run(trials_override=args.trials)
        print("\n====================================================")
        print("EXPERIMENT 23 COMPLETED SUCCESSFULLY")
        print("====================================================\n")
    else:
        print(f"Experiment '{args.experiment}' requested.")
        print("Supported experiments: '00', '01', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'.")

if __name__ == "__main__":
    main()
