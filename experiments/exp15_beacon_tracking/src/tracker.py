import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from generator.camera import PinholeCamera
from experiments.exp07_localization.src.roi_extractor import ROIExtractor
from experiments.exp07_localization.src.gaussian_fitting import GaussianFittingLocalization
from experiments.exp07_localization.src.intensity_weighted_centroid import IntensityWeightedCentroidLocalization
from experiments.exp10_psf_mismatch.src.psf_aware_fitting import PSFAwareFittingLocalization


class FSOCBeaconTracker:
    """
    Sequence Tracker for FSOC Virtual Camera Testbed.
    Combines a Constant Velocity Kalman Filter state predictor with adaptive ROI subpixel localization,
    validation gating, track state management, and reacquisition metrics.
    """
    def __init__(
        self,
        camera: PinholeCamera,
        estimator_type: str = "Gaussian Fitting",
        roi_size: int = 31,
        gating_threshold_px: float = 15.0,
        fps: float = 30.0,
        process_noise_q: float = 1.0,
        measurement_noise_r: float = 0.2,
        psf_sigma: float = 2.0
    ):
        self.camera = camera
        self.estimator_type = estimator_type
        self.roi_size = roi_size
        self.gating_threshold = gating_threshold_px
        self.fps = fps
        self.dt = 1.0 / fps
        self.q_var = process_noise_q
        self.r_var = measurement_noise_r
        self.psf_sigma = psf_sigma

        # Instantiate subpixel localization engine
        if estimator_type == "Intensity-Weighted Centroid":
            self.subpixel_engine = IntensityWeightedCentroidLocalization()
        elif estimator_type == "PSF Fitting":
            self.subpixel_engine = PSFAwareFittingLocalization(sigma_x=psf_sigma, sigma_y=psf_sigma)
        else:
            self.subpixel_engine = GaussianFittingLocalization()

        self.roi_extractor = ROIExtractor(roi_size=roi_size)
        self.reset()

    def reset(self):
        """Resets tracker state machine and Kalman filter state."""
        self.state = "INITIALIZING"  # State machine: INITIALIZING, TRACKING, LOST, REACQUIRING
        self.x_state = np.zeros(4, dtype=np.float64)  # [x, y, vx, vy]^T
        self.P_cov = np.eye(4, dtype=np.float64) * 100.0

        # State transition matrix F
        self.F = np.array([
            [1.0, 0.0, self.dt, 0.0],
            [0.0, 1.0, 0.0, self.dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float64)

        # Measurement matrix H
        self.H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float64)

        # Process noise covariance Q
        q = self.q_var
        dt = self.dt
        self.Q = q * np.array([
            [dt**4 / 4, 0.0, dt**3 / 2, 0.0],
            [0.0, dt**4 / 4, 0.0, dt**3 / 2],
            [dt**3 / 2, 0.0, dt**2, 0.0],
            [0.0, dt**3 / 2, 0.0, dt**2]
        ], dtype=np.float64)

        # Measurement noise covariance R
        self.R = np.eye(2, dtype=np.float64) * self.r_var

        self.frames_tracked = 0
        self.frames_lost = 0
        self.consecutive_lost_frames = 0
        self.reacquisition_frames = 0
        self.is_reacquiring = False
        self.loss_event_active = False

    def predict(self) -> Tuple[float, float]:
        """Kalman filter prediction step."""
        if self.state in ["TRACKING", "REACQUIRING", "LOST"]:
            self.x_state = self.F @ self.x_state
            self.P_cov = self.F @ self.P_cov @ self.F.T + self.Q

        return float(self.x_state[0]), float(self.x_state[1])

    def process_frame(
        self,
        frame: np.ndarray,
        x_gt: float,
        y_gt: float,
        is_occluded_gt: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single frame in the sequence:
        1. Predict target location
        2. Extract candidate ROI around prediction (or GT initialization)
        3. Perform subpixel localization
        4. Apply measurement gating check
        5. Update Kalman filter state and state machine
        6. Return frame-level performance record
        """
        start_time = time.perf_counter()

        # Step 1: Prediction
        if self.state == "INITIALIZING":
            # Initialize state at ground truth location
            self.x_state[0] = x_gt
            self.x_state[1] = y_gt
            self.x_state[2] = 0.0
            self.x_state[3] = 0.0
            self.P_cov = np.eye(4, dtype=np.float64) * 5.0
            pred_x, pred_y = x_gt, y_gt
        else:
            pred_x, pred_y = self.predict()

        # Bound prediction to image dimensions
        pred_x = np.clip(pred_x, self.roi_size // 2 + 1, self.camera.width - self.roi_size // 2 - 1)
        pred_y = np.clip(pred_y, self.roi_size // 2 + 1, self.camera.height - self.roi_size // 2 - 1)

        # Step 2: Extract ROI at predicted position
        roi_crop = self.roi_extractor.extract_roi(frame, pred_x, pred_y)

        # Step 3: Subpixel localization
        loc_res = self.subpixel_engine.localize(
            roi_crop, psf_family="gaussian", sigma_x=self.psf_sigma, sigma_y=self.psf_sigma
        )

        meas_valid = False
        x_est, y_est = None, None
        gate_dist = np.inf

        if loc_res.success and loc_res.x_est is not None and not np.isnan(loc_res.x_est) and not is_occluded_gt:
            x_candidate = float(loc_res.x_est)
            y_candidate = float(loc_res.y_est)

            # Measure distance from prediction
            gate_dist = float(np.sqrt((x_candidate - pred_x)**2 + (y_candidate - pred_y)**2))

            if gate_dist <= self.gating_threshold:
                meas_valid = True
                x_est = x_candidate
                y_est = y_candidate

        # Step 4: Kalman Update & State Machine
        if meas_valid:
            z = np.array([x_est, y_est], dtype=np.float64)
            y_innov = z - (self.H @ self.x_state)
            S_cov = self.H @ self.P_cov @ self.H.T + self.R
            K_gain = self.P_cov @ self.H.T @ np.linalg.inv(S_cov)

            self.x_state = self.x_state + K_gain @ y_innov
            self.P_cov = (np.eye(4) - K_gain @ self.H) @ self.P_cov

            if self.state in ["INITIALIZING", "LOST", "REACQUIRING"]:
                if self.loss_event_active:
                    # Reacquisition successful!
                    self.loss_event_active = False
                self.state = "TRACKING"

            self.frames_tracked += 1
            self.consecutive_lost_frames = 0

        else:
            # Measurement failed or gated out
            self.frames_lost += 1
            self.consecutive_lost_frames += 1

            if self.state == "TRACKING":
                self.state = "LOST"
                self.loss_event_active = True
                self.reacquisition_frames = 0
            elif self.state == "LOST" and self.loss_event_active:
                self.reacquisition_frames += 1

            # Estimate defaults to prediction during loss
            x_est = pred_x
            y_est = pred_y

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Compute position error e(t)
        err_x = float(x_est - x_gt)
        err_y = float(y_est - y_gt)
        pos_error_px = float(np.sqrt(err_x**2 + err_y**2))

        # Compute angular pointing error e_theta(t)
        tx_gt, ty_gt = self.camera.pixel_to_angle(x_gt, y_gt)
        tx_est, ty_est = self.camera.pixel_to_angle(x_est, y_est)
        e_tx = float(tx_est - tx_gt)
        e_ty = float(ty_est - ty_gt)
        angular_error_rad = float(np.sqrt(e_tx**2 + e_ty**2))
        angular_error_urad = float(angular_error_rad * 1e6)

        return {
            "x_gt": x_gt,
            "y_gt": y_gt,
            "pred_x": pred_x,
            "pred_y": pred_y,
            "x_est": x_est,
            "y_est": y_est,
            "pos_error_px": pos_error_px,
            "angular_error_urad": angular_error_urad,
            "gate_dist_px": gate_dist,
            "measurement_valid": meas_valid,
            "is_occluded_gt": is_occluded_gt,
            "track_state": self.state,
            "latency_ms": elapsed_ms,
            "consecutive_lost_frames": self.consecutive_lost_frames,
            "loss_event_active": self.loss_event_active
        }
