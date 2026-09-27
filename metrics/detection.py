import numpy as np

def compute_detection_metrics(tp: int, fp: int, fn: int, num_non_beacons: int = 1) -> dict:
    """
    Computes detection performance metrics with explicit scientific definitions:
    
    1. Detection Probability (Recall / True Positive Rate):
       P_D = TP / (TP + FN)
       Denominator: Total ground-truth beacon targets present in evaluation set.

    2. False Alarm Rate (P_FA):
       P_FA = FP / max(1, num_non_beacons)
       Denominator: Total number of non-beacon evaluation units / candidate regions evaluated.

    3. Precision:
       Precision = TP / max(1, TP + FP)
       Denominator: Total positive detections declared by system.

    4. F1-Score:
       F1 = 2 * Precision * Recall / max(1e-9, Precision + Recall)
       Harmonic mean of precision and recall.

    5. Miss Rate:
       Miss Rate = 1 - P_D = FN / (TP + FN)
    """
    total_actual = tp + fn
    pd = float(tp / total_actual) if total_actual > 0 else 0.0
    pfa = float(fp / max(1, num_non_beacons))
    precision = float(tp / max(1, tp + fp))
    recall = pd
    if precision + recall > 0:
        f1 = float(2.0 * precision * recall / (precision + recall))
    else:
        f1 = 0.0

    return {
        "P_D": pd,
        "P_FA": pfa,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "miss_rate": 1.0 - pd,
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "num_non_beacons": int(num_non_beacons)
    }
