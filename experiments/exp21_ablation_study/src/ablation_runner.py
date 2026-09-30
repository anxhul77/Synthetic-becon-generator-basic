import numpy as np
from typing import Dict, Any, List, Tuple

from experiments.exp19_fixed_vs_adaptive_eal.src.eal_search import (
    generate_fixed_eal,
    generate_adaptive_eal,
    check_acquisition,
    compute_search_path_length
)
from experiments.exp20_prediction_error_adaptation.src.innovation_adaptation import generate_error_adaptive_eal

def run_ablation_trial(
    center_u: float,
    center_v: float,
    Sigma_5: np.ndarray,
    nis_history: List[float],
    target_u_fut: np.ndarray,
    target_v_fut: np.ndarray,
    A_fixed: float = 150.0,
    gamma: float = 2.4477,
    lambda_adapt: float = 12.5,
    A_max: float = 350.0,
    duration_sec: float = 5.0,
    fps: float = 30.0,
    acq_radius: float = 15.0,
    consec_frames: int = 3,
    image_center_u: float = 960.0,
    image_center_v: float = 540.0
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates Methods A, B, C, D on identical trajectory inputs and search duration.
    """
    results = {}

    # Method A: Fixed EAL (No prediction center, centered at image center or last known position)
    eal_A = generate_fixed_eal(cx=image_center_u, cy=image_center_v, A_fixed=A_fixed, duration_sec=duration_sec, fps=fps)
    acq_frame_A, acq_t_A = check_acquisition(eal_A["u"], eal_A["v"], target_u_fut, target_v_fut, acq_radius=acq_radius, consec_frames=consec_frames, fps=fps)
    len_A = compute_search_path_length(eal_A["u"], eal_A["v"])
    results["Method A"] = {"u": eal_A["u"], "v": eal_A["v"], "acq_frame": acq_frame_A, "acq_t": acq_t_A, "path_len": len_A}

    # Method B: Predictive Fixed EAL (Search centered at 5-second prediction center, fixed amplitude)
    eal_B = generate_fixed_eal(cx=center_u, cy=center_v, A_fixed=A_fixed, duration_sec=duration_sec, fps=fps)
    acq_frame_B, acq_t_B = check_acquisition(eal_B["u"], eal_B["v"], target_u_fut, target_v_fut, acq_radius=acq_radius, consec_frames=consec_frames, fps=fps)
    len_B = compute_search_path_length(eal_B["u"], eal_B["v"])
    results["Method B"] = {"u": eal_B["u"], "v": eal_B["v"], "acq_frame": acq_frame_B, "acq_t": acq_t_B, "path_len": len_B}

    # Method C: Uncertainty-Adaptive EAL (Search centered at 5s prediction, covariance shape aligned)
    eal_C = generate_adaptive_eal(cx=center_u, cy=center_v, Sigma_5=Sigma_5, gamma=gamma, duration_sec=duration_sec, fps=fps)
    acq_frame_C, acq_t_C = check_acquisition(eal_C["u"], eal_C["v"], target_u_fut, target_v_fut, acq_radius=acq_radius, consec_frames=consec_frames, fps=fps)
    len_C = compute_search_path_length(eal_C["u"], eal_C["v"])
    results["Method C"] = {"u": eal_C["u"], "v": eal_C["v"], "acq_frame": acq_frame_C, "acq_t": acq_t_C, "path_len": len_C}

    # Method D: Full Adaptive EAL (Prediction center + covariance shape + observable NIS error adaptation)
    eal_D = generate_error_adaptive_eal(
        cx=center_u, cy=center_v, Sigma_5=Sigma_5, nis_history=nis_history,
        gamma=gamma, lambda_adapt=lambda_adapt, A_max=A_max, duration_sec=duration_sec, fps=fps
    )
    acq_frame_D, acq_t_D = check_acquisition(eal_D["u"], eal_D["v"], target_u_fut, target_v_fut, acq_radius=acq_radius, consec_frames=consec_frames, fps=fps)
    len_D = compute_search_path_length(eal_D["u"], eal_D["v"])
    results["Method D"] = {"u": eal_D["u"], "v": eal_D["v"], "acq_frame": acq_frame_D, "acq_t": acq_t_D, "path_len": len_D}

    return results
