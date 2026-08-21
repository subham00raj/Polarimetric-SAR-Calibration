from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class PolSARImage:
    """Four complex linear-polarization channels in user-facing order."""

    hh: np.ndarray
    hv: np.ndarray
    vh: np.ndarray
    vv: np.ndarray

    def __post_init__(self) -> None:
        self.hh = np.asarray(self.hh, dtype=np.complex128)
        self.hv = np.asarray(self.hv, dtype=np.complex128)
        self.vh = np.asarray(self.vh, dtype=np.complex128)
        self.vv = np.asarray(self.vv, dtype=np.complex128)
        self.validate()

    @property
    def shape(self) -> tuple[int, ...]:
        return self.hh.shape

    @property
    def rows(self) -> int:
        return self.hh.shape[0]

    @property
    def cols(self) -> int:
        return self.hh.shape[1]

    def validate(self) -> None:
        shapes = {self.hh.shape, self.hv.shape, self.vh.shape, self.vv.shape}
        if len(shapes) != 1:
            raise ValueError("HH, HV, VH, VV must have identical shapes.")
        if self.hh.ndim != 2:
            raise ValueError("PolSAR channels must be 2-D arrays.")

    def row(self, index: int) -> "PolSARImage":
        return PolSARImage(
            self.hh[index], self.hv[index], self.vh[index], self.vv[index]
        )

    def save(self, directory: str) -> None:
        from pathlib import Path

        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        np.save(output / "HH.npy", self.hh)
        np.save(output / "HV.npy", self.hv)
        np.save(output / "VH.npy", self.vh)
        np.save(output / "VV.npy", self.vv)


@dataclass(frozen=True, slots=True)
class CrosstalkParameters:
    u: complex
    v: complex
    w: complex
    z: complex
    alpha: complex


@dataclass(slots=True)
class IterationRecord:
    iteration: int
    du: complex
    dv: complex
    dw: complex
    dz: complex
    u: complex
    v: complex
    w: complex
    z: complex
    alpha: complex
    gamma: float


@dataclass(slots=True)
class AinsworthResult:
    parameters: CrosstalkParameters
    sigma: np.ndarray
    calibrated_covariance: np.ndarray
    iterations: int
    gamma: float
    converged: bool
    history: list[IterationRecord] = field(default_factory=list)


@dataclass(slots=True)
class ValidationResult:
    beta: float
    beta_prime: float
    eta: float
    eta_over_beta: float
    is_positive_definite: bool
    eigenvalues: np.ndarray
    crosstalk_magnitudes: dict[str, float]
    linearization_valid: bool
    hermitian_residual: float
    passed: bool


@dataclass(slots=True)
class RangeLineResult:
    row: int
    valid_count: int
    ainsworth: AinsworthResult
    validation: ValidationResult


@dataclass(slots=True)
class CalibrationDiagnostics:
    u_raw: np.ndarray
    v_raw: np.ndarray
    w_raw: np.ndarray
    z_raw: np.ndarray
    alpha_raw: np.ndarray
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray
    z: np.ndarray
    alpha: np.ndarray
    gamma: np.ndarray
    iterations: np.ndarray
    valid_pixels: np.ndarray
    converged: np.ndarray
    validation_passed: np.ndarray
    sigma: list[np.ndarray | None]
    config: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "u_raw": self.u_raw,
            "v_raw": self.v_raw,
            "w_raw": self.w_raw,
            "z_raw": self.z_raw,
            "alpha_raw": self.alpha_raw,
            "u": self.u,
            "v": self.v,
            "w": self.w,
            "z": self.z,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "iterations": self.iterations,
            "valid_pixels": self.valid_pixels,
            "converged": self.converged,
            "validation_passed": self.validation_passed,
            "sigma": self.sigma,
            "stripe_half_width": self.config.stripe_half_width,
            "correlation_threshold": self.config.correlation_threshold,
            "smoothing_window": self.config.smoothing_window,
            "max_iter": self.config.max_iterations,
            "tolerance": self.config.tolerance,
        }
