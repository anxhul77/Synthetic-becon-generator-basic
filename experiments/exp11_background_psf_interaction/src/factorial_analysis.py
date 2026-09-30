import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Tuple

def compute_factorial_interaction_contrasts(df_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 2-way and 3-way interaction contrasts across PSF width, SNR, and Background level for each estimator.
    """
    rows = []

    methods = df_summary["method_name"].unique() if "method_name" in df_summary.columns else df_summary["method"].unique()

    for method in methods:
        method_col = "method_name" if "method_name" in df_summary.columns else "method"
        df_m = df_summary[df_summary[method_col] == method]
        if df_m.empty:
            continue

        # 1. PSF x SNR Interaction Contrast (at fixed background levels)
        for bg in df_m["background_level"].unique():
            df_bg = df_m[df_m["background_level"] == bg]
            sig_min, sig_max = df_bg["psf_sigma_px"].min(), df_bg["psf_sigma_px"].max()
            snr_min, snr_max = df_bg["snr_db"].min(), df_bg["snr_db"].max()

            r_sigMax_snrMin = df_bg[(df_bg["psf_sigma_px"] == sig_max) & (df_bg["snr_db"] == snr_min)]["radial_rmse"].values
            r_sigMax_snrMax = df_bg[(df_bg["psf_sigma_px"] == sig_max) & (df_bg["snr_db"] == snr_max)]["radial_rmse"].values
            r_sigMin_snrMin = df_bg[(df_bg["psf_sigma_px"] == sig_min) & (df_bg["snr_db"] == snr_min)]["radial_rmse"].values
            r_sigMin_snrMax = df_bg[(df_bg["psf_sigma_px"] == sig_min) & (df_bg["snr_db"] == snr_max)]["radial_rmse"].values

            if len(r_sigMax_snrMin) > 0 and len(r_sigMax_snrMax) > 0 and len(r_sigMin_snrMin) > 0 and len(r_sigMin_snrMax) > 0:
                v_max = r_sigMax_snrMin[0] - r_sigMax_snrMax[0]
                v_min = r_sigMin_snrMin[0] - r_sigMin_snrMax[0]
                contrast = float(v_max - v_min)
                rows.append({
                    "method": method,
                    "factor_pair": "PSF_x_SNR",
                    "conditioning_factor": f"Background={bg:g}DN",
                    "contrast_formula": f"(RMSE(sig={sig_max}, snr={snr_min}) - RMSE(sig={sig_max}, snr={snr_max})) - (RMSE(sig={sig_min}, snr={snr_min}) - RMSE(sig={sig_min}, snr={snr_max}))",
                    "interaction_contrast": contrast,
                    "effect_interpretation": "Non-zero indicates effect of SNR on RMSE changes with PSF width",
                    "sample_count": len(df_bg)
                })

        # 2. PSF x Background Interaction Contrast (at fixed SNR levels)
        for snr in df_m["snr_db"].unique():
            df_snr = df_m[df_m["snr_db"] == snr]
            sig_min, sig_max = df_snr["psf_sigma_px"].min(), df_snr["psf_sigma_px"].max()
            bg_min, bg_max = df_snr["background_level"].min(), df_snr["background_level"].max()

            r_sigMax_bgMax = df_snr[(df_snr["psf_sigma_px"] == sig_max) & (df_snr["background_level"] == bg_max)]["radial_rmse"].values
            r_sigMax_bgMin = df_snr[(df_snr["psf_sigma_px"] == sig_max) & (df_snr["background_level"] == bg_min)]["radial_rmse"].values
            r_sigMin_bgMax = df_snr[(df_snr["psf_sigma_px"] == sig_min) & (df_snr["background_level"] == bg_max)]["radial_rmse"].values
            r_sigMin_bgMin = df_snr[(df_snr["psf_sigma_px"] == sig_min) & (df_snr["background_level"] == bg_min)]["radial_rmse"].values

            if len(r_sigMax_bgMax) > 0 and len(r_sigMax_bgMin) > 0 and len(r_sigMin_bgMax) > 0 and len(r_sigMin_bgMin) > 0:
                v_max = r_sigMax_bgMax[0] - r_sigMax_bgMin[0]
                v_min = r_sigMin_bgMax[0] - r_sigMin_bgMin[0]
                contrast = float(v_max - v_min)
                rows.append({
                    "method": method,
                    "factor_pair": "PSF_x_Background",
                    "conditioning_factor": f"SNR={snr:g}dB",
                    "contrast_formula": f"(RMSE(sig={sig_max}, bg={bg_max}) - RMSE(sig={sig_max}, bg={bg_min})) - (RMSE(sig={sig_min}, bg={bg_max}) - RMSE(sig={sig_min}, bg={bg_min}))",
                    "interaction_contrast": contrast,
                    "effect_interpretation": "Non-zero indicates sensitivity to background intensity depends on PSF width",
                    "sample_count": len(df_snr)
                })

        # 3. SNR x Background Interaction Contrast (at fixed PSF widths)
        for sig in df_m["psf_sigma_px"].unique():
            df_sig = df_m[df_m["psf_sigma_px"] == sig]
            snr_min, snr_max = df_sig["snr_db"].min(), df_sig["snr_db"].max()
            bg_min, bg_max = df_sig["background_level"].min(), df_sig["background_level"].max()

            r_snrMin_bgMax = df_sig[(df_sig["snr_db"] == snr_min) & (df_sig["background_level"] == bg_max)]["radial_rmse"].values
            r_snrMin_bgMin = df_sig[(df_sig["snr_db"] == snr_min) & (df_sig["background_level"] == bg_min)]["radial_rmse"].values
            r_snrMax_bgMax = df_sig[(df_sig["snr_db"] == snr_max) & (df_sig["background_level"] == bg_max)]["radial_rmse"].values
            r_snrMax_bgMin = df_sig[(df_sig["snr_db"] == snr_max) & (df_sig["background_level"] == bg_min)]["radial_rmse"].values

            if len(r_snrMin_bgMax) > 0 and len(r_snrMin_bgMin) > 0 and len(r_snrMax_bgMax) > 0 and len(r_snrMax_bgMin) > 0:
                v_min = r_snrMin_bgMax[0] - r_snrMin_bgMin[0]
                v_max = r_snrMax_bgMax[0] - r_snrMax_bgMin[0]
                contrast = float(v_min - v_max)
                rows.append({
                    "method": method,
                    "factor_pair": "SNR_x_Background",
                    "conditioning_factor": f"PSF_sigma={sig:g}px",
                    "contrast_formula": f"(RMSE(snr={snr_min}, bg={bg_max}) - RMSE(snr={snr_min}, bg={bg_min})) - (RMSE(snr={snr_max}, bg={bg_max}) - RMSE(snr={snr_max}, bg={bg_min}))",
                    "interaction_contrast": contrast,
                    "effect_interpretation": "Non-zero indicates background degradation severity amplifies at low SNR",
                    "sample_count": len(df_sig)
                })

    return pd.DataFrame(rows)


def fit_factorial_linear_model(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Fits Ordinary Least Squares (OLS) factorial regression model on localization squared radial error:
    e_r^2 ~ 1 + PSF_sigma + SNR_dB + Background + (PSF*SNR) + (PSF*BG) + (SNR*BG) + (PSF*SNR*BG)
    for each localization estimator.
    """
    results = []

    method_col = "method_name" if "method_name" in df_raw.columns else "method"
    methods = df_raw[method_col].unique()

    for method in methods:
        df_sub = df_raw[(df_raw[method_col] == method) & (df_raw["success"] == True)].copy()
        if len(df_sub) < 10:
            continue

        y = df_sub["radial_error_px"].values ** 2
        sig = df_sub["psf_sigma_px"].values
        snr = df_sub["snr_db"].values
        bg = df_sub["background_level"].values

        # Normalize factors for numeric stability
        sig_n = (sig - np.mean(sig)) / (np.std(sig) + 1e-12)
        snr_n = (snr - np.mean(snr)) / (np.std(snr) + 1e-12)
        bg_n = (bg - np.mean(bg)) / (np.std(bg) + 1e-12)

        X = np.column_stack([
            np.ones_like(y),
            sig_n,
            snr_n,
            bg_n,
            sig_n * snr_n,
            sig_n * bg_n,
            snr_n * bg_n,
            sig_n * snr_n * bg_n
        ])

        term_names = [
            "Intercept",
            "PSF_sigma",
            "SNR_dB",
            "Background_level",
            "PSF_x_SNR",
            "PSF_x_Background",
            "SNR_x_Background",
            "PSF_x_SNR_x_Background"
        ]

        try:
            beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            n, p = X.shape
            y_hat = X @ beta
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - y_hat) ** 2)
            r_squared = float(1.0 - (ss_res / (ss_tot + 1e-12)))

            mse = ss_res / max(1, n - p)
            var_beta = mse * np.linalg.pinv(X.T @ X).diagonal()
            se = np.sqrt(np.maximum(0, var_beta))

            for idx, name in enumerate(term_names):
                b_val = float(beta[idx])
                se_val = float(se[idx])
                t_stat = float(b_val / se_val) if se_val > 0 else 0.0
                p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=n - p)))
                ci_low = b_val - 1.96 * se_val
                ci_high = b_val + 1.96 * se_val

                results.append({
                    "method": method,
                    "factor_term": name,
                    "coefficient": b_val,
                    "std_error": se_val,
                    "t_statistic": t_stat,
                    "p_value": p_val,
                    "ci_95_lower": ci_low,
                    "ci_95_upper": ci_high,
                    "r_squared": r_squared,
                    "sample_size": n
                })
        except Exception as e:
            print(f"Factorial OLS fitting warning for {method}: {e}")

    return pd.DataFrame(results)
