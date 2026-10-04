import numpy as np
from typing import List, Tuple

DEFAULT_PHASE_STEPS = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]

def generate_controlled_phase_grid(steps: List[float] = None) -> List[Tuple[float, float]]:
    """
    Generates 64 controlled subpixel phase grid combinations (phi_x, phi_y).
    """
    if steps is None:
        steps = DEFAULT_PHASE_STEPS
    elif isinstance(steps, (int, np.integer)):
        if int(steps) < 1:
            raise ValueError("phase grid step count must be positive")
        steps = np.arange(int(steps), dtype=np.float64) / float(int(steps))
    grid = []
    for px in steps:
        for py in steps:
            grid.append((float(px), float(py)))
    return grid

def assign_phase_bin(phi: float, num_bins: int = 8) -> float:
    """
    Maps continuous fractional phase phi in [0, 1) to the nearest discrete phase step.
    """
    bin_size = 1.0 / num_bins
    bin_idx = int(np.floor((phi % 1.0) / bin_size + 0.5)) % num_bins
    return float(bin_idx * bin_size)
