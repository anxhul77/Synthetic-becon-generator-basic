import pytest
import numpy as np
from experiments.exp22_monte_carlo_validation.src.stats_analyzer import (
    compute_paired_stats,
    compute_cohens_d
)

def test_cohens_d():
    x1 = np.array([10.0, 12.0, 11.0, 13.0, 10.5])
    x2 = np.array([5.0, 6.0, 5.5, 7.0, 6.5])

    d = compute_cohens_d(x1, x2)
    assert d > 2.0  # Large positive effect size

def test_paired_stats():
    x_a = np.array([0.5, 0.6, 0.4, 0.55, 0.5])
    x_d = np.array([0.9, 0.95, 0.85, 0.9, 0.95])

    res = compute_paired_stats(x_a, x_d)
    assert "mean_diff" in res
    assert "p_value" in res
    assert "cohens_d" in res
    assert res["mean_diff"] > 0  # Method D higher than Method A
