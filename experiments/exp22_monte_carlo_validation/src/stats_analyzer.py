import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Tuple

def compute_cohens_d(x1: np.ndarray, x2: np.ndarray) -> float:
    """
    Computes Cohen's d effect size for paired or independent samples.
    """
    x1 = np.asarray(x1, dtype=np.float64)
    x2 = np.asarray(x2, dtype=np.float64)

    n1, n2 = len(x1), len(x2)
    s1, s2 = np.var(x1, ddof=1), np.var(x2, ddof=1)

    pooled_std = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled_std < 1e-12:
        return 0.0
    return float((np.mean(x1) - np.mean(x2)) / pooled_std)

def compute_paired_stats(x_baseline: np.ndarray, x_proposed: np.ndarray) -> Dict[str, Any]:
    """
    Performs paired statistical analysis:
    1. Mean, median, std, 95% CIs
    2. Shapiro-Wilk normality test
    3. Paired t-test or Wilcoxon signed-rank test
    4. Cohen's d effect size
    """
    xb = np.asarray(x_baseline, dtype=np.float64)
    xp = np.asarray(x_proposed, dtype=np.float64)

    diff = xp - xb
    mean_diff = float(np.mean(diff))
    median_diff = float(np.median(diff))
    std_diff = float(np.std(diff, ddof=1))

    n = len(diff)
    se_diff = std_diff / np.sqrt(n) if n > 0 else 0.0
    ci_low = mean_diff - 1.96 * se_diff
    ci_high = mean_diff + 1.96 * se_diff

    # Shapiro-Wilk normality check on differences
    if n >= 3 and np.var(diff) > 1e-12:
        _, p_norm = stats.shapiro(diff)
    else:
        p_norm = 1.0

    # Paired test selection
    if np.all(diff == 0):
        stat, p_val = 0.0, 1.0
        test_type = "Identical Data"
    elif p_norm > 0.05:
        stat, p_val = stats.ttest_rel(xp, xb)
        test_type = "Paired t-test"
    else:
        stat, p_val = stats.wilcoxon(xp, xb)
        test_type = "Wilcoxon Signed-Rank"

    cohen_d = compute_cohens_d(xp, xb)

    return {
        "n": n,
        "mean_diff": mean_diff,
        "median_diff": median_diff,
        "std_diff": std_diff,
        "ci_lower": float(ci_low),
        "ci_upper": float(ci_high),
        "p_normality": float(p_norm),
        "test_type": test_type,
        "statistic": float(stat),
        "p_value": float(p_val),
        "cohens_d": cohen_d
    }
