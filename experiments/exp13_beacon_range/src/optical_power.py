"""
Physical Traceable Optical Link Budget & Operating Envelope Evaluator for FSOC Terminals.

Link Model Parameters:
- Wavelength lambda (nm) [Default: 1550 nm]
- Transmit Power P_tx (mW) [Default: 500 mW]
- Beam Waist w0 (m) [Default: 0.025 m]
- Receiver Aperture D_rx (m) [Default: 0.10 m]
- Atmospheric Attenuation gamma (km^-1) [Kruse/Kim & Rain Models]
- Visibility Range V (km)
- Turbulence Strength Cn2 (m^-2/3)
- Scattering Fraction eta
- Detector Sensitivity / Noise Floor (DN) [Minimum detectable signal amplitude I_min]
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from generator.atmosphere import kruse_attenuation_alpha, rain_attenuation_alpha


class OpticalLinkRangeModel:
    """
    Traceable Gaussian Optical Link Budget Model.
    """
    def __init__(
        self,
        wavelength_nm: float = 1550.0,
        transmit_power_mw: float = 500.0,
        beam_waist_m: float = 0.025,
        receiver_aperture_m: float = 0.10,
        optical_efficiency: float = 0.80,
        reference_range_km: float = 1.0,
        reference_amplitude_dn: float = 150.0,
        detector_noise_floor_dn: float = 3.0
    ):
        self.wavelength_m = float(wavelength_nm * 1e-9)
        self.wavelength_nm = float(wavelength_nm)
        self.p_tx_mw = float(transmit_power_mw)
        self.w0 = float(beam_waist_m)
        self.d_rx = float(receiver_aperture_m)
        self.eta_opt = float(optical_efficiency)
        self.ref_l_km = float(max(0.001, reference_range_km))
        self.ref_amp_dn = float(reference_amplitude_dn)
        self.noise_floor_dn = float(detector_noise_floor_dn)

        # Rayleigh range z_R = pi * w0^2 / lambda
        self.z_R_m = float(np.pi * (self.w0**2) / self.wavelength_m)

        # Reference captured power ratio at 1 km clear sky (V = 23 km)
        ref_gamma = kruse_attenuation_alpha(self.wavelength_nm, 23.0)
        ref_w_L = self.calculate_beam_radius(self.ref_l_km)
        r_rx = self.d_rx / 2.0
        ref_p_cap = 1.0 - np.exp(-2.0 * (r_rx**2) / (ref_w_L**2))
        ref_p_rx = self.p_tx_mw * self.eta_opt * ref_p_cap * np.exp(-ref_gamma * self.ref_l_km)

        # Detector responsivity scale factor K_sens (DN / mW)
        self.k_sens = self.ref_amp_dn / max(1e-6, ref_p_rx)

    def calculate_beam_radius(self, range_km: float) -> float:
        """Calculates Gaussian beam radius w(L) = w0 * sqrt(1 + (L / z_R)^2) in meters."""
        L_m = float(range_km * 1000.0)
        return float(self.w0 * np.sqrt(1.0 + (L_m / self.z_R_m)**2))

    def calculate_captured_power_ratio(self, range_km: float) -> float:
        """
        Calculates captured power fraction over circular receiver aperture of diameter D_rx:
        P_ratio = 1 - exp(-2 * (D_rx / 2)^2 / w(L)^2)
        """
        w_L = self.calculate_beam_radius(range_km)
        r_rx = self.d_rx / 2.0
        p_ratio = 1.0 - np.exp(-2.0 * (r_rx**2) / (w_L**2))
        return float(self.eta_opt * p_ratio)

    def calculate_received_optical_power_mw(self, range_km: float, attenuation_alpha_km: float) -> float:
        """Calculates received optical power P_rx(L) = P_tx * captured_ratio * exp(-gamma * L) in mW."""
        p_cap = self.calculate_captured_power_ratio(range_km)
        transmittance = np.exp(-attenuation_alpha_km * range_km)
        return float(self.p_tx_mw * p_cap * transmittance)

    def calculate_received_amplitude_dn(self, range_km: float, attenuation_alpha_km: float) -> float:
        """Calculates received peak signal amplitude in Digital Numbers (DN)."""
        p_rx = self.calculate_received_optical_power_mw(range_km, attenuation_alpha_km)
        amp_dn = self.k_sens * p_rx
        return float(max(0.0, amp_dn))


class OperatingEnvelopeEvaluator:
    """
    Evaluates scenario-specific Operating Envelope compliance for FSOC trackers:
    Criteria:
    1. Minimum Detection Probability P_D >= 95%
    2. Maximum False Alarm Probability P_FA <= 1%
    3. Maximum Angular RMSE <= 100 urad
    4. Minimum Received Amplitude >= Detector Sensitivity Limit (I_min = 10.5 DN)
    """
    def __init__(
        self,
        min_p_detection: float = 0.95,
        max_p_false_alarm: float = 0.01,
        max_angular_rmse_urad: float = 100.0,
        min_signal_amplitude_dn: float = 10.5
    ):
        self.min_p_det = float(min_p_detection)
        self.max_p_fa = float(max_p_false_alarm)
        self.max_ang_rmse = float(max_angular_rmse_urad)
        self.min_amp_dn = float(min_signal_amplitude_dn)

    def evaluate_compliance(
        self,
        p_detection: float,
        p_false_alarm: float,
        angular_rmse_urad: float,
        received_amplitude_dn: float = 150.0
    ) -> Dict[str, Any]:
        p_det_valid = bool(p_detection >= self.min_p_det)
        p_fa_valid = bool(p_false_alarm <= self.max_p_fa)
        ang_valid = bool(angular_rmse_urad is not None and not np.isnan(angular_rmse_urad) and angular_rmse_urad <= self.max_ang_rmse)
        amp_valid = bool(received_amplitude_dn >= self.min_amp_dn)

        is_compliant = bool(p_det_valid and p_fa_valid and ang_valid and amp_valid)

        return {
            "p_detection_compliant": p_det_valid,
            "p_false_alarm_compliant": p_fa_valid,
            "angular_rmse_compliant": ang_valid,
            "amplitude_compliant": amp_valid,
            "is_fully_compliant": is_compliant
        }
