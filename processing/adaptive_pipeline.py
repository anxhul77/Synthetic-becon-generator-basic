"""
Modern Adaptive Optical Beacon Detector & Preprocessing Pipeline for FSOC Terminals.

Implements the reframed detection pipeline incorporating:
1. Background-normalized intensity transformation
2. Adaptive statistical & CFAR-style dynamic thresholding (CA-CFAR)
3. Connected-component geometric gating
4. Multi-feature candidate confidence scoring engine
5. Temporal persistence tracking & noise spike rejection
6. Explicit sensor saturation failure management
"""

import time
import numpy as np
import cv2
from scipy import ndimage
from processing.localization import intensity_weighted_centroid


class BackgroundNormalizer:
    """
    Background Normalization Engine.
    Estimates local/global baseline radiance mu_B and noise scale sigma_B,
    producing background-normalized intensity arrays.
    Uses fast float32 2D box filtering for sub-millisecond execution.
    """
    def __init__(self, blur_sigma: float = 15.0):
        self.blur_sigma = float(blur_sigma)

    def normalize(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        img_f32 = image.astype(np.float32)
        ksize = int(np.ceil(4.0 * self.blur_sigma))
        if ksize % 2 == 0:
            ksize += 1
        ksize = max(3, ksize)

        mu_b = cv2.boxFilter(img_f32, -1, (ksize, ksize), borderType=cv2.BORDER_REFLECT)
        residual = img_f32 - mu_b
        diff_sq = residual * residual
        sigma_b_map = cv2.boxFilter(diff_sq, -1, (ksize, ksize), borderType=cv2.BORDER_REFLECT)
        sigma_b = np.sqrt(np.maximum(1e-4, sigma_b_map))

        i_norm = (residual / sigma_b).astype(np.float32)
        return i_norm, mu_b, sigma_b


class AdaptiveCFARDetector:
    """
    Cell-Averaging Constant False Alarm Rate (CA-CFAR) Thresholding Engine.
    Computes spatially adaptive threshold map T(x,y) = mu_ref(x,y) + alpha * sigma_ref(x,y).
    """
    def __init__(self, guard_win: int = 5, ref_win: int = 15, pfa_target: float = 1e-4, alpha: float = None):
        self.guard_win = int(guard_win) if guard_win % 2 != 0 else int(guard_win) + 1
        self.ref_win = int(ref_win) if ref_win % 2 != 0 else int(ref_win) + 1
        self.pfa_target = float(pfa_target)
        # Dynamic multiplier alpha if not explicitly specified (derived from P_FA target under Gaussian assumption)
        if alpha is not None:
            self.alpha = float(alpha)
        else:
            from scipy.stats import norm
            self.alpha = float(norm.ppf(1.0 - pfa_target))

    def detect_mask(self, image: np.ndarray, mu_b: np.ndarray = None, sigma_b: np.ndarray = None) -> tuple[np.ndarray, np.ndarray]:
        img_f = image.astype(np.float64)

        if mu_b is None or sigma_b is None:
            # Fast box filter sliding window background statistics
            ksize = self.ref_win
            mu_ref = cv2.boxFilter(img_f, -1, (ksize, ksize), borderType=cv2.BORDER_REFLECT)
            sq_ref = cv2.boxFilter(img_f ** 2, -1, (ksize, ksize), borderType=cv2.BORDER_REFLECT)
            sigma_ref = np.sqrt(np.maximum(1e-4, sq_ref - mu_ref ** 2))
        else:
            mu_ref = mu_b
            sigma_ref = sigma_b

        t_map = mu_ref + self.alpha * sigma_ref
        binary_mask = (img_f > t_map).astype(np.uint8)
        return binary_mask, t_map


class TemporalPersistenceTracker:
    """
    Temporal Persistence Engine.
    Tracks candidate detections across frame sequences to boost true target confidence
    and filter out isolated single-frame salt-and-pepper / noise spikes.
    """
    def __init__(self, max_track_dist: float = 15.0, history_length: int = 5):
        self.max_track_dist = float(max_track_dist)
        self.history_length = int(history_length)
        self.tracks = []  # list of track dicts: {"centroid": (x, y), "history": [(x, y)], "hits": count}

    def reset(self):
        self.tracks = []

    def update(self, candidates: list[dict]) -> list[dict]:
        """
        Updates candidate scores with temporal persistence hits.
        """
        if not candidates:
            # Decay tracks
            for t in self.tracks:
                t["hits"] = max(0, t["hits"] - 1)
            self.tracks = [t for t in self.tracks if t["hits"] > 0]
            return candidates

        updated_candidates = []
        for cand in candidates:
            cx, cy = cand["x_est"], cand["y_est"]
            best_dist = float("inf")
            best_track_idx = -1

            for i, tr in enumerate(self.tracks):
                tx, ty = tr["centroid"]
                dist = np.hypot(cx - tx, cy - ty)
                if dist < best_dist and dist <= self.max_track_dist:
                    best_dist = dist
                    best_track_idx = i

            cand_copy = dict(cand)
            if best_track_idx >= 0:
                # Matched existing temporal track
                tr = self.tracks[best_track_idx]
                tr["centroid"] = (cx, cy)
                tr["hits"] = min(self.history_length, tr["hits"] + 1)
                tr["history"].append((cx, cy))
                if len(tr["history"]) > self.history_length:
                    tr["history"].pop(0)
                cand_copy["temporal_hits"] = tr["hits"]
                cand_copy["persistence_score"] = float(tr["hits"] / self.history_length)
            else:
                # New track candidate
                self.tracks.append({"centroid": (cx, cy), "history": [(cx, cy)], "hits": 1})
                cand_copy["temporal_hits"] = 1
                cand_copy["persistence_score"] = float(1.0 / self.history_length)

            updated_candidates.append(cand_copy)

        return updated_candidates


class ReframedBeaconDetector:
    """
    Reframed Modern Optical Beacon Detector Pipeline.
    
    Integrated Pipeline:
    1. Saturation Check: Explicit failure reporting if sensor pixels saturate (>5% clipped to 255).
    2. Background Normalization: Computes Z-score intensity relative to spatially varying background.
    3. CA-CFAR Adaptive Thresholding: Dynamic thresholding adapted to noise distribution.
    4. Connected Component Extraction & Gating: Size (5-20 px target size), aspect ratio, circularity bounds.
    5. Multi-Feature Candidate Scoring: Computes composite confidence score S_conf in [0, 1].
    6. Temporal Persistence Filtering: Validates track persistence across sequential frames.
    7. Subpixel Centroid Estimation: Intensity-weighted centroid over top-confidence candidate.
    """
    def __init__(self,
                 target_size_px: float = 10.0,
                 min_area: int = 3,
                 max_area: int = 80,
                 max_aspect_ratio: float = 2.2,
                 min_circularity: float = 0.35,
                 cfar_alpha: float = 3.5,
                 blur_sigma: float = 15.0,
                 min_confidence: float = 0.15,
                 enable_temporal: bool = False):

        self.target_size_px = float(target_size_px)
        self.min_area = int(min_area)
        self.max_area = int(max_area)
        self.max_aspect_ratio = float(max_aspect_ratio)
        self.min_circularity = float(min_circularity)
        self.min_confidence = float(min_confidence)
        self.enable_temporal = enable_temporal

        self.normalizer = BackgroundNormalizer(blur_sigma=blur_sigma)
        self.cfar_detector = AdaptiveCFARDetector(alpha=cfar_alpha)
        self.temporal_tracker = TemporalPersistenceTracker() if enable_temporal else None

    def reset_temporal_state(self):
        if self.temporal_tracker is not None:
            self.temporal_tracker.reset()

    def detect(self, image: np.ndarray, beacon_gt: tuple[float, float] = None, tolerance_px: float = 5.0) -> dict:
        t0 = time.perf_counter()
        img_arr = np.asarray(image)
        h, w = img_arr.shape

        # 1. Saturation Check (Dynamic range failure detection)
        sat_mask = (img_arr >= 255)
        sat_pixel_count = int(np.sum(sat_mask))
        sat_fraction = float(sat_pixel_count / (h * w))
        
        is_saturated = bool(sat_fraction > 0.05)
        if is_saturated:
            # Saturation treated explicitly as an operational failure case
            t1 = time.perf_counter()
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "saturation_failure": True,
                "sat_fraction": sat_fraction,
                "confidence": 0.0,
                "total_latency_ms": (t1 - t0) * 1000.0
            }

        # 2. Background Normalization
        i_norm, mu_b, sigma_b = self.normalizer.normalize(img_arr)

        # 3. CA-CFAR Dynamic Adaptive Thresholding
        binary_mask, t_map = self.cfar_detector.detect_mask(img_arr, mu_b=mu_b, sigma_b=sigma_b)

        # 4. Connected Component Extraction
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)

        if num_labels <= 1:
            t1 = time.perf_counter()
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "saturation_failure": False,
                "sat_fraction": sat_fraction,
                "confidence": 0.0,
                "total_latency_ms": (t1 - t0) * 1000.0
            }

        cand_indices = np.arange(1, num_labels)
        areas = stats[cand_indices, cv2.CC_STAT_AREA]

        # Fast pre-filtering by target area bounds to eliminate 99%+ noise blobs before expensive feature extraction
        valid_area_mask = (areas >= self.min_area) & (areas <= self.max_area)
        if not np.any(valid_area_mask):
            t1 = time.perf_counter()
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "saturation_failure": False,
                "sat_fraction": sat_fraction,
                "confidence": 0.0,
                "total_latency_ms": (t1 - t0) * 1000.0
            }

        valid_indices = cand_indices[valid_area_mask]
        areas = areas[valid_area_mask]
        lefts = stats[valid_indices, cv2.CC_STAT_LEFT]
        tops = stats[valid_indices, cv2.CC_STAT_TOP]
        widths = stats[valid_indices, cv2.CC_STAT_WIDTH]
        heights = stats[valid_indices, cv2.CC_STAT_HEIGHT]
        valid_centroids = centroids[valid_indices]

        # Extract peaks strictly on valid size components
        peaks = ndimage.maximum(img_arr, labels, index=valid_indices)
        sums = ndimage.sum_labels(img_arr, labels, index=valid_indices)

        min_dims = np.minimum(widths, heights)
        max_dims = np.maximum(widths, heights)
        aspect_ratios = np.where(min_dims > 0, max_dims / min_dims, 1.0)
        perimeters = 2.0 * (widths + heights)
        circularities = np.where(perimeters > 0, (4.0 * np.pi * areas) / (perimeters ** 2), 0.0)

        # 5. Connected Component Gating & Feature Extraction
        candidates = []
        for i, idx in enumerate(valid_indices):
            area = int(areas[i])
            ar = float(aspect_ratios[i])
            circ = float(circularities[i])

            if ar > self.max_aspect_ratio:
                continue
            if circ < self.min_circularity:
                continue

            left = int(lefts[i])
            top = int(tops[i])
            w_b = int(widths[i])
            h_b = int(heights[i])
            bbox = (left, top, left + w_b, top + h_b)

            cx = float(valid_centroids[i, 0])
            cy = float(valid_centroids[i, 1])

            local_mu = float(np.mean(mu_b[top:top+h_b, left:left+w_b]))
            local_sig = float(np.mean(sigma_b[top:top+h_b, left:left+w_b]))

            peak_val = float(peaks[i])
            contrast = (peak_val - local_mu) / max(1e-3, local_sig)

            # Candidate Confidence Score Formula S_conf in [0, 1]
            s_snr = min(1.0, max(0.0, contrast / 10.0))
            s_shape = circ * (1.0 - 0.5 * min(1.0, abs(ar - 1.0)))
            s_area = np.exp(-((area - self.target_size_px) ** 2) / (2.0 * (15.0 ** 2)))
            
            s_conf = 0.45 * s_snr + 0.35 * s_shape + 0.20 * s_area

            if s_conf < self.min_confidence:
                continue

            candidates.append({
                "label": int(idx),
                "bbox": bbox,
                "area": area,
                "aspect_ratio": ar,
                "circularity": circ,
                "peak": peak_val,
                "sum": float(sums[i]),
                "contrast": contrast,
                "confidence": float(s_conf),
                "x_est": cx,
                "y_est": cy,
                "temporal_hits": 1,
                "persistence_score": 1.0
            })

        # 6. Optional Temporal Persistence Filter
        if self.enable_temporal and self.temporal_tracker is not None:
            candidates = self.temporal_tracker.update(candidates)
            # Combine confidence with persistence
            for c in candidates:
                c["confidence"] = 0.70 * c["confidence"] + 0.30 * c["persistence_score"]

        num_cand = len(candidates)
        if num_cand == 0:
            t1 = time.perf_counter()
            return {
                "detected": False,
                "x_est": None,
                "y_est": None,
                "num_candidates": 0,
                "matching_count": 0,
                "false_candidate_count": 0,
                "primary_candidate": None,
                "candidates": [],
                "saturation_failure": False,
                "sat_fraction": sat_fraction,
                "confidence": 0.0,
                "total_latency_ms": (t1 - t0) * 1000.0
            }

        # 7. Select Primary Candidate by Highest Composite Confidence Score
        best_cand = max(candidates, key=lambda c: c["confidence"])

        # Subpixel intensity-weighted centroid over primary ROI
        xc, yc = intensity_weighted_centroid(img_arr, roi_bbox=best_cand["bbox"])
        best_cand["x_est"] = float(xc)
        best_cand["y_est"] = float(yc)

        # Match against ground truth if supplied
        matching_count = 0
        false_candidate_count = num_cand
        if beacon_gt is not None:
            bx, by = beacon_gt
            cand_coords = np.array([[c["x_est"], c["y_est"]] for c in candidates])
            dists = np.hypot(cand_coords[:, 0] - bx, cand_coords[:, 1] - by)
            matching_mask = dists <= tolerance_px
            matching_count = int(np.sum(matching_mask))
            false_candidate_count = int(num_cand - matching_count)

        t1 = time.perf_counter()
        total_latency_ms = (t1 - t0) * 1000.0

        return {
            "detected": True,
            "x_est": float(xc),
            "y_est": float(yc),
            "num_candidates": num_cand,
            "matching_count": matching_count,
            "false_candidate_count": false_candidate_count,
            "primary_candidate": best_cand,
            "candidates": candidates,
            "saturation_failure": False,
            "sat_fraction": sat_fraction,
            "confidence": float(best_cand["confidence"]),
            "total_latency_ms": total_latency_ms
        }
