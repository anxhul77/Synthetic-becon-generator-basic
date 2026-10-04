"""
Deterministic Unit Tests for Acquisition and Reacquisition Metrics (Priority 2E).
"""

import pytest
import numpy as np
from processing.shared_metrics import (
    compute_acquisition_time,
    compute_reacquisition_time,
    compute_lock_breakdown
)


def test_acquisition_immediate_lock():
    """TEST 1: Target visible from frame 0 and valid immediately (N=3)."""
    fps = 30.0
    hit_mask = [True, True, True, True, True]
    acq_t = compute_acquisition_time(hit_mask, fps=fps, min_consecutive=3)
    # Lock confirmed at index 2 -> 2 / 30 = 0.0667 s
    assert pytest.approx(acq_t, 1e-4) == 2.0 / 30.0
    assert acq_t > 0.0


def test_acquisition_delayed_appearance():
    """TEST 2: Target becomes detectable at frame 10."""
    fps = 30.0
    hit_mask = [False] * 10 + [True, True, True, True]
    acq_t = compute_acquisition_time(hit_mask, fps=fps, min_consecutive=3)
    # Lock confirmed at index 12 -> 12 / 30 = 0.4 s
    assert pytest.approx(acq_t, 1e-4) == 12.0 / 30.0


def test_acquisition_intermittent_fails_criterion():
    """TEST 3: One valid detection followed by two invalid frames (N=3). NO ACQUISITION."""
    fps = 30.0
    hit_mask = [True, False, False, True, False, False]
    acq_t = compute_acquisition_time(hit_mask, fps=fps, min_consecutive=3)
    assert np.isnan(acq_t)


def test_reacquisition_temporary_loss_recovery():
    """TEST 4: Tracking lost for 5 frames then recovered."""
    fps = 30.0
    # 5 hits, 5 misses, 3 hits
    hit_mask = [True] * 5 + [False] * 5 + [True] * 3
    reacq_t = compute_reacquisition_time(hit_mask, fps=fps, min_consecutive=3)
    assert isinstance(reacq_t, float)
    # Loss started at frame 5, recovery confirmed at frame 12 -> 7 frames = 7/30 s
    assert pytest.approx(reacq_t, 1e-4) == 7.0 / 30.0


def test_reacquisition_never_returned():
    """TEST 5: Target lost and never returns."""
    fps = 30.0
    hit_mask = [True] * 5 + [False] * 10
    reacq_t = compute_reacquisition_time(hit_mask, fps=fps, min_consecutive=3)
    assert reacq_t == "FAILED"


def test_reacquisition_never_lost():
    """TEST 6: Target never leaves lock."""
    fps = 30.0
    hit_mask = [True] * 20
    reacq_t = compute_reacquisition_time(hit_mask, fps=fps, min_consecutive=3)
    assert reacq_t == "NOT_APPLICABLE"


def test_lock_breakdown():
    """TEST 7: Lock breakdown calculation."""
    states = ["SEARCHING", "REACQUIRING", "TRACKING", "TRACKING", "COASTING", "LOST"]
    breakdown = compute_lock_breakdown(states)
    assert breakdown["total_frames"] == 6
    assert breakdown["locked_frames"] == 2
    assert breakdown["searching_frames"] == 1
    assert breakdown["coasting_frames"] == 1
    assert breakdown["reacquiring_frames"] == 1
    assert breakdown["lost_frames"] == 1
    assert pytest.approx(breakdown["lock_retention_pct"], 1e-2) == (2.0 / 6.0) * 100.0
