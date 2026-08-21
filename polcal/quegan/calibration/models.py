from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from polcal.ainsworth.calibration.models import PolSARImage

__all__ = [
    "PolSARImage",
    "CrosstalkParameters",
    "QueganResult",
    "ValidationResult",
    "RangeLineResult",
    "CalibrationDiagnostics",
]


@dataclass(frozen=True, slots=True)
class CrosstalkParameters:
    """Solution of Quegan (1994) eqs. (22)-(30) for one range line."""

    u: complex
    v: complex
    w: complex
    z: complex
    alpha: complex
    beta: complex
    alpha1: complex
    beta1: complex
    alpha2: complex
    beta2: complex


@dataclass(slots=True)
class QueganResult:
    parameters: CrosstalkParameters
    calibration_matrix: np.ndarray
    calibrated_covariance: np.ndarray


@dataclass(slots=True)
class ValidationResult:
    is_positive_definite: bool
    eigenvalues: np.ndarray
    crosstalk_magnitudes: dict[str, float]
    linearization_valid: bool
    alpha_solution_disagreement: float
    hermitian_residual: float
    passed: bool


@dataclass(slots=True)
class RangeLineResult:
    row: int
    valid_count: int
    quegan: QueganResult
    validation: ValidationResult


@dataclass(slots=True)
class CalibrationDiagnostics:
    u_raw: np.ndarray
    v_raw: np.ndarray
    w_raw: np.ndarray
    z_raw: np.ndarray
    alpha_raw: np.ndarray
    beta_raw: np.ndarray
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray
    z: np.ndarray
    alpha: np.ndarray
    beta: np.ndarray
    alpha1: np.ndarray
    alpha2: np.ndarray
    valid_pixels: np.ndarray
    validation_passed: np.ndarray
    calibration_matrix: list[np.ndarray | None] = field(default_factory=list)
    config: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "u_raw": self.u_raw,
            "v_raw": self.v_raw,
            "w_raw": self.w_raw,
            "z_raw": self.z_raw,
            "alpha_raw": self.alpha_raw,
            "beta_raw": self.beta_raw,
            "u": self.u,
            "v": self.v,
            "w": self.w,
            "z": self.z,
            "alpha": self.alpha,
            "beta": self.beta,
            "alpha1": self.alpha1,
            "alpha2": self.alpha2,
            "valid_pixels": self.valid_pixels,
            "validation_passed": self.validation_passed,
            "stripe_half_width": self.config.stripe_half_width,
            "correlation_threshold": self.config.correlation_threshold,
            "smoothing_window": self.config.smoothing_window,
            "solution": self.config.solution,
        }
