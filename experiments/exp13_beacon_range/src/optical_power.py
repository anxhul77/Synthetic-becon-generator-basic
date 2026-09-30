import numpy as np
from typing import Dict, Any, Tuple, Optional

class OpticalLinkRangeModel:
    """
    Gaussian Optical Link Spreading & Power Model.
    Calculates distance-dependent Gaussian beam expansion w(L), Rayleigh range z_R,
    captured optical power ratio over receiver aperture D_rx, and received synthetic image amplitude.
    """
    def __init__(
        self,
        wavelength_nm: float = 1550.0,
        beam_waist_m: float = 0.05,
        receiver_aperture_m: float = 0.10,
        optical_efficiency: float = 0.80,
        reference_range_km: float = 1.0
    ):
        self.wavelength_m = float(wavelength_nm * 1e-9)
        self.w0 = float(beam_waist_m)
        self.d_rx = float(receiver_aperture_m)
        self.eta = float(optical_efficiency)
        self.ref_l_m = float(max(0.001, reference_range_km * 1000.0))

        # Rayleigh range z_R = pi * w0^2 / lambda
        self.z_R_m = float(np.pi * (self.w0**2) / self.wavelength_m)

    def calculate_beam_radius(self, range_km: float) -> float:
        """Calculates Gaussian beam radius w(L) = w0 * sqrt(1 + (L / z_R)^2) in meters."""
        L_m = float(range_km * 1000.0)
        w_L = self.w0 * np.sqrt(1.0 + (L_m / self.z_R_m)**2)
        return float(w_L)

    def calculate_captured_power_ratio(self, range_km: float) -> float:
        """
        Calculates captured power fraction over circular receiver aperture of diameter D_rx:
        P_ratio = 1 - exp(-2 * (D_rx / 2)^2 / w(L)^2)
        """
        w_L = self.calculate_beam_radius(range_km)
        r_rx = self.d_rx / 2.0
        p_ratio = 1.0 - np.exp(-2.0 * (r_rx**2) / (w_L**2))
        return float(self.eta * p_ratio)

    def calculate_received_amplitude(
        self,
        initial_amplitude: float,
        range_km: float,
        transmittance: float = 1.0
    ) -> float:
        """
        Maps captured optical power ratio to synthetic image peak amplitude:
        A_received(L) = A0 * [P_captured(L) / P_captured(L_ref)] * transmittance
        """
        if range_km <= 0.0:
            return float(initial_amplitude)

        p_ref = self.calculate_captured_power_ratio(self.ref_l_m / 1000.0)
        p_curr = self.calculate_captured_power_ratio(range_km)

        if p_ref <= 0.0:
            power_factor = 1.0
        else:
            power_factor = p_curr / p_ref

        amp_rec = initial_amplitude * power_factor * transmittance
        return float(max(0.0, amp_rec))


class OperatingEnvelopeEvaluator:
    """
    Evaluates whether a test condition satisfies FSOC tracker requirements:
    1. Minimum Detection Probability P_D >= 95%
    2. Maximum False Alarm Probability P_FA <= 1%
    3. Maximum Angular RMSE <= 100 urad
    """
    def __init__(
        self,
        min_p_detection: float = 0.95,
        max_p_false_alarm: float = 0.01,
        max_angular_rmse_urad: float = 100.0
    ):
        self.min_p_det = float(min_p_detection)
        self.max_p_fa = float(max_p_false_alarm)
        self.max_ang_rmse = float(max_angular_rmse_urad)

    def evaluate_compliance(
        self,
        p_detection: float,
        p_false_alarm: float,
        angular_rmse_urad: float
    ) -> Dict[str, Any]:
        p_det_valid = bool(p_detection >= self.min_p_det)
        p_fa_valid = bool(p_false_alarm <= self.max_p_fa)
        ang_valid = bool(angular_rmse_urad is not None and not np.isnan(angular_rmse_urad) and angular_rmse_urad <= self.max_ang_rmse)

        is_compliant = bool(p_det_valid and p_fa_valid and ang_valid)

        return {
            "p_detection_compliant": p_det_valid,
            "p_false_alarm_compliant": p_fa_valid,
            "angular_rmse_compliant": ang_valid,
            "is_fully_compliant": is_compliant
        }
