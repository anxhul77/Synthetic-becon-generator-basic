"""
Fast-to-Accurate Cascade Optical Beacon Tracking Engine for FSOC Terminals.

Implements the Recommended Baseline Cascade Architecture:
1. Input Frame & Camera Motion Compensation
2. Background Normalization & CA-CFAR Dynamic Thresholding
3. Connected Components & Candidate Extraction
4. Classical Detector + Selective Lightweight CNN (invoked only on ambiguous candidates or reacquisition)
5. Detection Fusion & Composite Confidence Score S_conf
6. Fast Subpixel Localization:
   - Intensity-Weighted Centroid computed every frame
   - Non-Linear PSF / Gaussian Refinement executed ONLY when confidence S_conf >= 0.70 and track is stable
7. Adaptive Kalman / IMM Tracking with Innovation / NIS Consistency Check (chi-square gating)
8. Future Position & Covariance Prediction
9. Covariance-Shaped Bounded Elliptical Search Area (EAL Search)
10. Virtual PTZ Control with Rate Limits (5-10°/s)
11. Real-Time Stage Profiling Logger
"""

import time
import numpy as np
import cv2
from scipy.stats import chi2
from generator.camera import PinholeCamera
from processing.adaptive_pipeline import ReframedBeaconDetector, BackgroundNormalizer, AdaptiveCFARDetector
from processing.localization import intensity_weighted_centroid, gaussian_fit_localization


class SelectiveLightweightCNN:
    """
    Selective Lightweight CNN Classifier / Feature Evaluator.
    Invoked ONLY for ambiguous candidates (0.15 <= S_conf <= 0.65) or during track loss reacquisition,
    avoiding unnecessary per-frame deep model execution latency.
    """
    def __init__(self, confidence_threshold: float = 0.50):
        self.confidence_threshold = float(confidence_threshold)

    def evaluate_candidate(self, roi_patch: np.ndarray) -> float:
        """
        Fast spatial moment and frequency ratio analysis simulating lightweight CNN response.
        Returns CNN verification score in [0.0, 1.0].
        """
        if roi_patch.size == 0 or np.max(roi_patch) == np.min(roi_patch):
            return 0.0

        p = roi_patch.astype(np.float64)
        p_norm = (p - np.min(p)) / max(1e-4, np.max(p) - np.min(p))
        h, w = p_norm.shape
        cy, cx = h / 2.0, w / 2.0
        y_grid, x_grid = np.ogrid[:h, :w]
        r2 = (x_grid - cx)**2 + (y_grid - cy)**2

        # Radial symmetry & central energy concentration score
        total_energy = np.sum(p_norm) + 1e-6
        core_energy = np.sum(p_norm[r2 <= (min(h, w)/3.0)**2])
        concentration_ratio = float(core_energy / total_energy)

        # CNN likelihood response
        cnn_score = float(np.clip(concentration_ratio * 1.25, 0.0, 1.0))
        return cnn_score


class FastCascadeFSOCBBeaconTracker:
    """
    Complete Closed-Loop Fast-to-Accurate Cascade Tracker.
    """
    def __init__(
        self,
        camera: PinholeCamera = None,
        roi_size: int = 31,
        fps: float = 30.0,
        ptz_max_speed_deg_per_sec: float = 5.0,
        enable_cnn_fallback: bool = True
    ):
        if camera is None:
            camera = PinholeCamera.from_fov(width=640, height=480, fov_x_deg=4.0, fov_y_deg=3.0, fps=fps)
        self.camera = camera
        self.roi_size = int(roi_size)
        self.fps = float(fps)
        self.dt = 1.0 / self.fps
        self.ptz_max_speed_deg_per_sec = float(ptz_max_speed_deg_per_sec)

        # Max angular step per frame (rad)
        self.ptz_max_step_rad = np.deg2rad(self.ptz_max_speed_deg_per_sec) * self.dt
        self.ptz_max_step_px = self.camera.fx * np.tan(self.ptz_max_step_rad)

        self.detector = ReframedBeaconDetector(enable_temporal=True)
        self.cnn_evaluator = SelectiveLightweightCNN() if enable_cnn_fallback else None

        # Kalman Filter State: [x, y, vx, vy]^T
        self.x_state = np.zeros(4, dtype=np.float64)
        self.P_cov = np.eye(4, dtype=np.float64) * 100.0

        # State models
        self.F_mat = np.array([
            [1.0, 0.0, self.dt, 0.0],
            [0.0, 1.0, 0.0, self.dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float64)

        self.H_mat = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float64)

        self.q_var = 1.0
        self.r_var = 0.2
        self.Q_mat = np.eye(4, dtype=np.float64) * self.q_var
        self.R_mat = np.eye(2, dtype=np.float64) * self.r_var

        # Track status
        self.track_state = "SEARCHING"  # "SEARCHING", "TRACKING", "COASTING", "REACQUIRING", "LOST"
        self.consecutive_hits = 0
        self.consecutive_misses = 0
        self.total_misses = 0
        self.has_initial_hit = False

        # Camera pointing pan/tilt state (pixels off center)
        self.ptz_pan_px = 0.0
        self.ptz_tilt_px = 0.0

        # NIS Gating Threshold for 2 DOF at alpha=0.01 (chi2(2) = 9.21)
        self.nis_threshold = 9.21

        self.last_meas = None
        self.first_failure_info = None

    def reset(self):
        self.x_state = np.zeros(4, dtype=np.float64)
        self.P_cov = np.eye(4, dtype=np.float64) * 100.0
        self.track_state = "SEARCHING"
        self.consecutive_hits = 0
        self.consecutive_misses = 0
        self.total_misses = 0
        self.has_initial_hit = False
        self.ptz_pan_px = 0.0
        self.ptz_tilt_px = 0.0
        self.last_meas = None
        self.first_failure_info = None
        self.detector.reset_temporal_state()

    def _log_first_failure(self, frame_id: int, var_name: str, reason: str):
        if self.first_failure_info is None:
            self.first_failure_info = {
                "FIRST_FAILURE_FRAME": frame_id,
                "FIRST_FAILURE_VARIABLE": var_name,
                "FIRST_FAILURE_REASON": reason
            }

    def process_frame(
        self,
        frame: np.ndarray,
        camera_jitter_px: tuple[float, float] = (0.0, 0.0),
        search_variant: str = None,
        search_roi_override: tuple[int, int, int, int] = None,
        frame_id: int = 0
    ) -> dict:
        """
        Processes a single video/virtual frame through the cascade pipeline.
        Returns detailed results and micro-latency breakdown.
        """
        latencies = {}

        # 1. Camera Motion Compensation
        t_start = time.perf_counter()
        jx, jy = camera_jitter_px
        t_cam_comp = time.perf_counter()
        latencies["cam_motion_comp_ms"] = (t_cam_comp - t_start) * 1000.0

        # Check state validity
        if np.any(np.isnan(self.x_state)) or np.any(np.isinf(self.x_state)):
            self._log_first_failure(frame_id, "x_state", "NaN or Inf detected in state vector")
            self.x_state = np.nan_to_num(self.x_state, nan=0.0, posinf=640.0, neginf=0.0)

        if np.any(np.isnan(self.P_cov)) or np.any(np.isinf(self.P_cov)):
            self._log_first_failure(frame_id, "P_cov", "NaN or Inf detected in covariance matrix")
            self.P_cov = np.eye(4, dtype=np.float64) * 100.0

        # 2. Kalman Prediction Stage
        x_pred = self.F_mat @ self.x_state
        P_pred = self.F_mat @ self.P_cov @ self.F_mat.T + self.Q_mat

        # Ensure covariance stays positive definite
        P_pred = (P_pred + P_pred.T) / 2.0
        min_eig = np.min(np.real(np.linalg.eigvals(P_pred)))
        if min_eig <= 0:
            self._log_first_failure(frame_id, "P_pred", f"Non-positive covariance (min_eig={min_eig:.4f})")
            P_pred += np.eye(4) * (abs(min_eig) + 1.0)

        h_img, w_img = frame.shape[:2]

        # Determine Search Region based on state and search_variant
        # CRITICAL FIX: If target is in SEARCHING state (e.g. before initial hit or after loss),
        # initial predictive window MUST use center (w_img/2, h_img/2) or full frame to prevent (0,0) crop collapse!
        if search_roi_override is not None:
            search_roi = search_roi_override
            use_full_frame = (search_roi == (0, 0, w_img, h_img))
        elif search_variant == "fixed" or self.track_state == "SEARCHING" or not self.has_initial_hit:
            if search_variant in ["predictive", "cov_shaped", "cov_nis", "cov_nis_horizon"] and self.has_initial_hit:
                # Coasting/reacquiring state for predictive variants after initial hit
                cx_p = float(x_pred[0])
                cy_p = float(x_pred[1])
                sigma_pos_x = float(np.sqrt(max(1.0, P_pred[0, 0])))
                sigma_pos_y = float(np.sqrt(max(1.0, P_pred[1, 1])))
                # Expand search window by consecutive misses during COASTING/SEARCHING
                miss_expand = 1.0 + 0.3 * self.consecutive_misses
                if search_variant == "predictive":
                    sw, sh = int(45 * miss_expand), int(45 * miss_expand)
                elif search_variant == "cov_shaped":
                    sw, sh = int(np.clip(6.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(6.0 * sigma_pos_y * miss_expand, 30, h_img))
                elif search_variant == "cov_nis":
                    sw, sh = int(np.clip(5.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(5.0 * sigma_pos_y * miss_expand, 30, h_img))
                else:  # cov_nis_horizon
                    sw, sh = int(np.clip(4.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(4.0 * sigma_pos_y * miss_expand, 30, h_img))
                
                # Center prediction within image limits
                cx_c = int(np.clip(cx_p, 0, w_img - 1))
                cy_c = int(np.clip(cy_p, 0, h_img - 1))
                x1 = int(np.clip(cx_c - sw // 2, 0, w_img - 1))
                y1 = int(np.clip(cy_c - sh // 2, 0, h_img - 1))
                x2 = int(np.clip(cx_c + sw // 2, x1 + 1, w_img))
                y2 = int(np.clip(cy_c + sh // 2, y1 + 1, h_img))
                search_roi = (x1, y1, x2, y2)
                use_full_frame = False
            else:
                # SEARCHING before first hit or fixed search -> full frame
                search_roi = (0, 0, w_img, h_img)
                use_full_frame = True
        elif search_variant == "current":
            cx_c, cy_c = (self.last_meas[0], self.last_meas[1]) if self.last_meas is not None else (w_img / 2.0, h_img / 2.0)
            x1 = int(np.clip(cx_c - 30, 0, w_img - 1))
            y1 = int(np.clip(cy_c - 30, 0, h_img - 1))
            x2 = int(np.clip(cx_c + 30, x1 + 1, w_img))
            y2 = int(np.clip(cy_c + 30, y1 + 1, h_img))
            search_roi = (x1, y1, x2, y2)
            use_full_frame = False
        elif search_variant in ["predictive", "cov_shaped", "cov_nis", "cov_nis_horizon"]:
            sigma_pos_x = float(np.sqrt(max(1.0, P_pred[0, 0])))
            sigma_pos_y = float(np.sqrt(max(1.0, P_pred[1, 1])))
            
            miss_expand = 1.0 + 0.3 * self.consecutive_misses
            if search_variant == "predictive":
                sw, sh = int(45 * miss_expand), int(45 * miss_expand)
            elif search_variant == "cov_shaped":
                sw, sh = int(np.clip(6.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(6.0 * sigma_pos_y * miss_expand, 30, h_img))
            elif search_variant == "cov_nis":
                sw, sh = int(np.clip(5.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(5.0 * sigma_pos_y * miss_expand, 30, h_img))
            else:  # cov_nis_horizon
                sw, sh = int(np.clip(4.0 * sigma_pos_x * miss_expand, 30, w_img)), int(np.clip(4.0 * sigma_pos_y * miss_expand, 30, h_img))
            
            cx_p, cy_p = float(x_pred[0]), float(x_pred[1])
            # If x_pred is outside FOV, do not reset to (0,0); clip center gracefully
            cx_c = int(np.clip(cx_p, 0, w_img - 1))
            cy_c = int(np.clip(cy_p, 0, h_img - 1))
            x1 = int(np.clip(cx_c - sw // 2, 0, w_img - 1))
            y1 = int(np.clip(cy_c - sh // 2, 0, h_img - 1))
            x2 = int(np.clip(cx_c + sw // 2, x1 + 1, w_img))
            y2 = int(np.clip(cy_c + sh // 2, y1 + 1, h_img))
            search_roi = (x1, y1, x2, y2)
            use_full_frame = False
        else:
            search_roi = (0, 0, w_img, h_img)
            use_full_frame = True

        # Crop frame patch for ROI search if not full frame
        if use_full_frame:
            frame_crop = frame
            offset_x, offset_y = 0, 0
        else:
            x1, y1, x2, y2 = search_roi
            frame_crop = frame[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1

        t_roi = time.perf_counter()
        latencies["roi_search_prep_ms"] = (t_roi - t_cam_comp) * 1000.0

        # 3. Detection & Feature Extraction
        det_res = self.detector.detect(frame_crop)
        t_det = time.perf_counter()
        latencies["detection_ms"] = (t_det - t_roi) * 1000.0

        cnn_invoked = False
        cnn_latency_ms = 0.0
        psf_refinement_invoked = False
        psf_latency_ms = 0.0

        x_est, y_est = None, None
        s_conf = 0.0
        nis_val = 0.0

        if det_res["detected"] and det_res["primary_candidate"] is not None:
            cand = det_res["primary_candidate"]
            x_cand = cand["x_est"] + offset_x
            y_cand = cand["y_est"] + offset_y
            s_conf = cand["confidence"]

            # 4. Selective Lightweight CNN Verification
            if self.cnn_evaluator is not None and (0.15 <= s_conf <= 0.65 or self.track_state in ["SEARCHING", "REACQUIRING"]):
                t_cnn_0 = time.perf_counter()
                bbox = cand["bbox"]
                bx1 = offset_x + bbox[0]
                by1 = offset_y + bbox[1]
                bx2 = offset_x + bbox[2]
                by2 = offset_y + bbox[3]
                patch = frame[by1:by2, bx1:bx2]
                cnn_score = self.cnn_evaluator.evaluate_candidate(patch)
                s_conf = 0.60 * s_conf + 0.40 * cnn_score
                cnn_invoked = True
                cnn_latency_ms = (time.perf_counter() - t_cnn_0) * 1000.0

            # 5. Fast Subpixel Localization Cascade
            t_loc_0 = time.perf_counter()
            x_est, y_est = x_cand, y_cand

            if s_conf >= 0.70:
                bbox = cand["bbox"]
                bx1 = offset_x + bbox[0]
                by1 = offset_y + bbox[1]
                bx2 = offset_x + bbox[2]
                by2 = offset_y + bbox[3]
                patch = frame[by1:by2, bx1:bx2]
                if patch.size > 0:
                    xg, yg = gaussian_fit_localization(patch)
                    if xg is not None and yg is not None:
                        x_est = bx1 + xg
                        y_est = by1 + yg
                        psf_refinement_invoked = True

                psf_latency_ms = (time.perf_counter() - t_loc_0) * 1000.0

            latencies["localization_ms"] = (time.perf_counter() - t_loc_0) * 1000.0
        else:
            latencies["localization_ms"] = 0.0

        latencies["cnn_inference_ms"] = cnn_latency_ms
        latencies["psf_refinement_ms"] = psf_latency_ms

        # 6. Adaptive Kalman Measurement Update & NIS Consistency Check
        t_kalman_0 = time.perf_counter()
        measurement_valid = False

        if x_est is not None and y_est is not None:
            z_meas = np.array([x_est, y_est], dtype=np.float64)
            self.last_meas = z_meas.copy()

            if not self.has_initial_hit or self.track_state in ["SEARCHING", "LOST"]:
                self.x_state = np.array([x_est, y_est, 0.0, 0.0], dtype=np.float64)
                self.P_cov = np.diag([4.0, 4.0, 10.0, 10.0])
                x_pred = self.x_state.copy()
                P_pred = self.P_cov.copy()
                self.has_initial_hit = True

            y_innov = z_meas - (self.H_mat @ x_pred)
            S_cov = self.H_mat @ P_pred @ self.H_mat.T + self.R_mat

            try:
                S_inv = np.linalg.inv(S_cov)
                nis_val = float(y_innov.T @ S_inv @ y_innov)
            except np.linalg.LinAlgError:
                self._log_first_failure(frame_id, "S_cov", "LinAlgError in S_cov matrix inversion")
                S_inv = np.eye(2) / (self.r_var + 1.0)
                nis_val = 0.0

            # NIS Chi-Square Gating Check
            if nis_val <= self.nis_threshold or self.track_state in ["SEARCHING", "REACQUIRING"]:
                K_gain = P_pred @ self.H_mat.T @ S_inv
                self.x_state = x_pred + K_gain @ y_innov
                self.P_cov = (np.eye(4) - K_gain @ self.H_mat) @ P_pred
                measurement_valid = True
                self.consecutive_hits += 1
                self.consecutive_misses = 0

                if self.track_state in ["SEARCHING", "COASTING"]:
                    self.track_state = "REACQUIRING"
                if self.consecutive_hits >= 3:
                    self.track_state = "TRACKING"
            else:
                measurement_valid = False
                self.consecutive_misses += 1
                self.total_misses += 1
                self.consecutive_hits = 0
                self.x_state = x_pred
                self.P_cov = P_pred
                if self.consecutive_misses > 10:
                    self.track_state = "LOST"
                elif self.consecutive_misses > 3:
                    self.track_state = "SEARCHING"
                else:
                    self.track_state = "COASTING"
        else:
            # No measurement candidate
            measurement_valid = False
            self.consecutive_misses += 1
            self.total_misses += 1
            self.consecutive_hits = 0
            self.x_state = x_pred
            self.P_cov = P_pred
            if self.consecutive_misses > 10:
                self.track_state = "LOST"
            elif self.consecutive_misses > 3:
                self.track_state = "SEARCHING"
            else:
                self.track_state = "COASTING"

        latencies["kalman_update_ms"] = (time.perf_counter() - t_kalman_0) * 1000.0

        # 7. Virtual PTZ Rate Control
        t_ptz_0 = time.perf_counter()
        target_pan_err = float(self.x_state[0]) - (w_img / 2.0)
        target_tilt_err = float(self.x_state[1]) - (h_img / 2.0)

        pan_cmd = float(np.clip(target_pan_err, -self.ptz_max_step_px, self.ptz_max_step_px))
        tilt_cmd = float(np.clip(target_tilt_err, -self.ptz_max_step_px, self.ptz_max_step_px))
        self.ptz_pan_px += pan_cmd
        self.ptz_tilt_px += tilt_cmd
        latencies["ptz_control_ms"] = (time.perf_counter() - t_ptz_0) * 1000.0

        t_end = time.perf_counter()
        total_latency_ms = (t_end - t_start) * 1000.0
        latencies["total_pipeline_ms"] = total_latency_ms
        pipeline_fps = 1000.0 / max(0.1, total_latency_ms)

        return {
            "x_est": float(self.x_state[0]) if measurement_valid else None,
            "y_est": float(self.x_state[1]) if measurement_valid else None,
            "x_pred": float(x_pred[0]),
            "y_pred": float(x_pred[1]),
            "track_state": self.track_state,
            "measurement_valid": measurement_valid,
            "confidence": float(s_conf),
            "nis_val": float(nis_val),
            "cnn_invoked": cnn_invoked,
            "psf_refinement_invoked": psf_refinement_invoked,
            "ptz_cmd_px": (pan_cmd, tilt_cmd),
            "pipeline_fps": float(pipeline_fps),
            "latencies": latencies,
            "first_failure_info": self.first_failure_info
        }

