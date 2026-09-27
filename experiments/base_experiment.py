import os
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class BaseExperiment:
    """
    Abstract Base Class for reproducible FSOC beacon tracking experiments.
    Provides standard trial recording, CSV/Parquet export, statistical analysis,
    figure plotting, and research report formatting.
    """
    def __init__(self, experiment_id: str, title: str, objective: str, hypothesis: str,
                 results_dir: str = "results", reports_dir: str = "reports"):
        self.experiment_id = experiment_id
        self.title = title
        self.objective = objective
        self.hypothesis = hypothesis
        self.results_dir = results_dir
        self.reports_dir = reports_dir

        self.exp_results_dir = os.path.join(self.results_dir, self.experiment_id)
        self.logs_dir = os.path.join(self.reports_dir, "experiment_logs")
        self.tables_dir = os.path.join(self.reports_dir, "tables")
        self.figures_dir = os.path.join(self.reports_dir, "figures")

        for d in [self.exp_results_dir, self.logs_dir, self.tables_dir, self.figures_dir]:
            os.makedirs(d, exist_ok=True)

        self.trials_data = []

    def log_trial(self, trial_dict: dict):
        """Records raw trial result."""
        self.trials_data.append(trial_dict)

    def save_raw_data(self) -> pd.DataFrame:
        """Saves raw trials to CSV and Parquet."""
        df = pd.DataFrame(self.trials_data)
        csv_path = os.path.join(self.exp_results_dir, f"{self.experiment_id}_raw_trials.csv")
        df.to_csv(csv_path, index=False)
        try:
            parquet_path = os.path.join(self.exp_results_dir, f"{self.experiment_id}_raw_trials.parquet")
            df.to_parquet(parquet_path, index=False)
        except Exception:
            pass
        return df

    def generate_report(self,
                        research_question: str,
                        materials_required: str,
                        software_tools: str,
                        hardware_info: str,
                        methods_tested: list[str],
                        input_parameters: dict,
                        independent_vars: str,
                        controlled_vars: str,
                        dependent_vars: str,
                        experimental_setup: str,
                        procedure: str,
                        ground_truth_desc: str,
                        calculations_desc: str,
                        error_formulas: str,
                        perf_metrics_desc: str,
                        observations: str,
                        failure_cases: str,
                        limitations: str,
                        conclusion: str,
                        arch_decision: str,
                        justification: str,
                        next_experiment: str) -> str:

        df = pd.DataFrame(self.trials_data)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        seeds = sorted(list(set(df["seed"].tolist()))) if "seed" in df.columns else []

        # Generate markdown result table
        methods = df["method"].unique() if "method" in df.columns else ["Default"]
        table_rows = []
        summary_lines = []

        for m in methods:
            m_df = df[df["method"] == m] if "method" in df.columns else df
            rmse_x = np.sqrt(np.mean(m_df["error_x"] ** 2)) if "error_x" in m_df.columns else 0.0
            rmse_y = np.sqrt(np.mean(m_df["error_y"] ** 2)) if "error_y" in m_df.columns else 0.0
            rmse_r = np.sqrt(np.mean(m_df["radial_error"] ** 2)) if "radial_error" in m_df.columns else 0.0
            ang_rmse = np.sqrt(np.mean(m_df["angular_error"] ** 2)) if "angular_error" in m_df.columns else 0.0
            pd_val = np.mean(m_df["detected"]) if "detected" in m_df.columns else 1.0
            pfa_val = np.mean(m_df["false_alarm"]) if "false_alarm" in m_df.columns else 0.0
            runtime_ms = np.mean(m_df["runtime_ms"]) if "runtime_ms" in m_df.columns else 0.0
            fps_val = np.mean(m_df["fps"]) if "fps" in m_df.columns else 0.0

            table_rows.append(
                f"| {m} | Baseline | {pd_val:.4f} | {pfa_val:.4f} | {rmse_x:.4f} | {rmse_y:.4f} | {rmse_r:.4f} | {ang_rmse:.6f} | {runtime_ms:.2f} | {fps_val:.1f} |"
            )
            summary_lines.append(
                f"Method: {m} | Radial RMSE: {rmse_r:.6f} px | Angular RMSE: {ang_rmse:.8f} rad | Mean Runtime: {runtime_ms:.3f} ms"
            )

        table_header = "| Method | Condition | P_D | P_FA | RMSE X | RMSE Y | Radial RMSE | Angular RMSE | Runtime | FPS |\n| ------ | --------- | --: | ---: | -----: | -----: | ----------: | -----------: | ------: | --: |"
        result_table_str = table_header + "\n" + "\n".join(table_rows)

        # Save result table to CSV/MD
        table_path = os.path.join(self.tables_dir, f"{self.experiment_id}_table.md")
        with open(table_path, "w", encoding="utf-8") as f:
            f.write(result_table_str)

        report_content = f"""====================================================
{self.experiment_id.upper()}
====================================================

TITLE: {self.title}

DATE: {now_str}

EXPERIMENT ID: {self.experiment_id}

OBJECTIVE: {self.objective}

RESEARCH QUESTION: {research_question}

HYPOTHESIS: {self.hypothesis}

MATERIALS REQUIRED: {materials_required}

SOFTWARE / TOOLS: {software_tools}

HARDWARE: {hardware_info}

METHODS / ALGORITHMS TESTED: {', '.join(methods_tested)}

INPUT PARAMETERS:
{json.dumps(input_parameters, indent=2)}

INDEPENDENT VARIABLES: {independent_vars}

CONTROLLED VARIABLES: {controlled_vars}

DEPENDENT VARIABLES: {dependent_vars}

DATASET SIZE: {len(df)} frames

NUMBER OF TRIALS: {len(df)}

RANDOM SEEDS: {seeds}

EXPERIMENTAL SETUP: {experimental_setup}

PROCEDURE: {procedure}

GROUND TRUTH: {ground_truth_desc}

CALCULATIONS: {calculations_desc}

ERROR FORMULAS: {error_formulas}

PERFORMANCE METRICS: {perf_metrics_desc}

RAW RESULTS: Saved to {os.path.abspath(os.path.join(self.exp_results_dir, f'{self.experiment_id}_raw_trials.csv'))}

STATISTICAL SUMMARY:
{chr(10).join(summary_lines)}

RESULT TABLE:
{result_table_str}

GRAPHS / FIGURES: Saved to {self.figures_dir}

OBSERVATIONS: {observations}

FAILURE CASES: {failure_cases}

LIMITATIONS: {limitations}

CONCLUSION: {conclusion}

ARCHITECTURE DECISION: {arch_decision}

JUSTIFICATION FOR DECISION: {justification}

NEXT EXPERIMENT: {next_experiment}
"""

        report_path = os.path.join(self.logs_dir, f"{self.experiment_id}_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"Report generated successfully: {report_path}")
        return report_content

    def run(self):
        raise NotImplementedError
