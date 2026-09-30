import numpy as np

def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """
    Computes 95% Wilson score confidence interval for proportion p = k / n.
    Handles boundary cases (k=0, k=n) gracefully.
    """
    if n <= 0:
        return 0.0, 0.0
    p_hat = float(k) / float(n)
    if confidence == 0.95:
        z = 1.959963984540054
    else:
        # Standard normal quantile
        from scipy.stats import norm
        z = norm.ppf(1.0 - (1.0 - confidence) / 2.0)

    denominator = 1.0 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2.0 * n)) / denominator
    spread = (z / denominator) * np.sqrt((p_hat * (1.0 - p_hat) / n) + ((z ** 2) / (4.0 * (n ** 2))))

    ci_lower = max(0.0, float(center - spread))
    ci_upper = min(1.0, float(center + spread))
    return ci_lower, ci_upper


def compute_bootstrap_rmse_ci(errors: np.ndarray, num_bootstraps: int = 1000, confidence: float = 0.95, seed: int = 42) -> tuple[float, float]:
    """
    Computes 95% percentile bootstrap confidence interval for RMSE from an array of errors.
    Returns (NaN, NaN) if len(errors) < 2.
    """
    arr = np.array(errors, dtype=np.float64)
    if len(arr) < 2:
        return float(np.nan), float(np.nan)

    rng = np.random.default_rng(seed)
    n = len(arr)
    boot_rmse = np.empty(num_bootstraps, dtype=np.float64)

    for i in range(num_bootstraps):
        resample = rng.choice(arr, size=n, replace=True)
        boot_rmse[i] = np.sqrt(np.mean(np.square(resample)))

    alpha = 1.0 - confidence
    lower_pct = (alpha / 2.0) * 100.0
    upper_pct = (1.0 - alpha / 2.0) * 100.0

    ci_lower = float(np.percentile(boot_rmse, lower_pct))
    ci_upper = float(np.percentile(boot_rmse, upper_pct))
    return ci_lower, ci_upper
