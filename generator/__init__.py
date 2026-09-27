"""
Ground-truth synthetic beacon generator module for FSOC camera tracking experiments.
"""

from .beacon import BeaconSignal
from .psf import PSFModel, GaussianPSF, EllipticalGaussianPSF
from .background import BackgroundModel, UniformBackground, GradientBackground
from .noise import NoiseModel, GaussianNoise
from .atmosphere import AtmosphericModel
from .camera import PinholeCamera
from .generator import SyntheticBeaconGenerator

__all__ = [
    "BeaconSignal",
    "PSFModel",
    "GaussianPSF",
    "EllipticalGaussianPSF",
    "BackgroundModel",
    "UniformBackground",
    "GradientBackground",
    "NoiseModel",
    "GaussianNoise",
    "AtmosphericModel",
    "PinholeCamera",
    "SyntheticBeaconGenerator",
]
