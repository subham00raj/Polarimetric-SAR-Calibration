from __future__ import annotations

import numpy as np

from polcal.ainsworth.calibration.config import AinsworthConfig
from polcal.ainsworth.calibration.core import AinsworthMath
from polcal.ainsworth.calibration.models import AinsworthResult, ValidationResult


class CalibrationValidator:
    """Validation checks for an Ainsworth-calibrated covariance matrix."""

    def __init__(self, config: AinsworthConfig | None = None) -> None:
        self.config = config or AinsworthConfig()
        self.math = AinsworthMath(self.config)

    def validate(self, result: AinsworthResult) -> ValidationResult:
        covariance = result.calibrated_covariance
        beta = float(np.real(covariance[1, 1]))
        beta_prime = float(np.real(covariance[2, 2]))
        eta = beta - beta_prime
        eta_over_beta = eta / beta if beta != 0 else np.inf

        herm = self.math.hermitian(covariance)
        eigenvalues = np.linalg.eigvalsh(herm)
        scale = max(float(np.max(np.abs(eigenvalues))), 1e-30)
        positive = bool(np.all(eigenvalues > -self.config.positive_definite_tolerance * scale))

        p = result.parameters
        magnitudes = {name: abs(value) for name, value in {
            "u": p.u, "v": p.v, "w": p.w, "z": p.z
        }.items()}
        linearization_valid = all(value < 1.0 for value in magnitudes.values())
        hermitian_residual = float(np.max(np.abs(covariance - covariance.conj().T)))
        passed = positive and linearization_valid and eta_over_beta < 1.0

        return ValidationResult(
            beta=beta,
            beta_prime=beta_prime,
            eta=eta,
            eta_over_beta=eta_over_beta,
            is_positive_definite=positive,
            eigenvalues=eigenvalues,
            crosstalk_magnitudes=magnitudes,
            linearization_valid=linearization_valid,
            hermitian_residual=hermitian_residual,
            passed=passed,
        )

    def idempotency_check(
        self, covariance: np.ndarray, atol: float | None = None
    ) -> dict[str, float | int | bool]:
        result = self.math.calibrate_covariance_iterative(covariance)
        atol = self.config.idempotency_atol if atol is None else atol
        identity_residual = float(np.max(np.abs(result.sigma - np.eye(4))))
        p = result.parameters
        crosstalk_residual = max(abs(p.u), abs(p.v), abs(p.w), abs(p.z))
        alpha_residual = abs(p.alpha - 1.0)
        return {
            "Sigma_identity_residual": identity_residual,
            "crosstalk_residual": float(crosstalk_residual),
            "alpha_residual": float(alpha_residual),
        }
