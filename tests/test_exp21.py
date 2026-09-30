import pytest
import numpy as np
from experiments.exp21_ablation_study.src.ablation_runner import run_ablation_trial

def test_ablation_methods_initialization():
    cx, cy = 960.0, 540.0
    Sigma_5 = np.array([[100.0, 0.0], [0.0, 25.0]])
    target_u = np.full(150, 1000.0)
    target_v = np.full(150, 550.0)

    res = run_ablation_trial(
        center_u=cx,
        center_v=cy,
        Sigma_5=Sigma_5,
        nis_history=[1.0, 1.5, 2.0],
        target_u_fut=target_u,
        target_v_fut=target_v,
        A_fixed=150.0,
        gamma=2.4477,
        lambda_adapt=12.5,
        A_max=350.0,
        duration_sec=5.0,
        fps=30.0,
        acq_radius=15.0,
        consec_frames=3
    )

    assert "Method A" in res
    assert "Method B" in res
    assert "Method C" in res
    assert "Method D" in res

    # Method A search center should be unpredicted image center (960, 540)
    # Method B search center should be predicted center (960, 540)
    assert res["Method A"]["path_len"] > 0
    assert res["Method D"]["path_len"] > 0
