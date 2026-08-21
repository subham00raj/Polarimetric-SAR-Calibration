from __future__ import annotations

import numpy as np

from polcal.quegan.calibration.config import QueganConfig
from polcal.quegan.calibration.core import QueganMath
from polcal.quegan.calibration.models import QueganResult, ValidationResult


class CalibrationValidator:
    """Validation checks for a Quegan-calibrated covariance matrix."""

    def __init__(self, config: QueganConfig | None = None) -> None:
        self.config = config or QueganConfig()
        self.math = QueganMath(self.config)

    def validate(self, result: QueganResult) -> ValidationResult:
        covariance = result.calibrated_covariance
        herm = self.math.hermitian(covariance)
        eigenvalues = np.linalg.eigvalsh(herm)
        scale = max(float(np.max(np.abs(eigenvalues))), 1e-30)
        positive = bool(np.all(eigenvalues > -self.config.positive_definite_tolerance * scale))

        p = result.parameters
        magnitudes = {name: abs(value) for name, value in {
            "u": p.u, "v": p.v, "w": p.w, "z": p.z
        }.items()}
        linearization_valid = all(value < 1.0 for value in magnitudes.values())

        # Quegan's two (alpha, beta) solutions are algebraically independent
        # roots of the same equations; large disagreement flags an unreliable
        # or noise-dominated range line (Section III of the paper).
        disagreement = abs(p.alpha1 - p.alpha2) / max(abs(p.alpha1), self.config.epsilon)

        hermitian_residual = float(np.max(np.abs(covariance - covariance.conj().T)))
        passed = positive and linearization_valid and disagreement < 1.0

        return ValidationResult(
            is_positive_definite=positive,
            eigenvalues=eigenvalues,
            crosstalk_magnitudes=magnitudes,
            linearization_valid=linearization_valid,
            alpha_solution_disagreement=float(disagreement),
            hermitian_residual=hermitian_residual,
            passed=passed,
        )

    def idempotency_check(self, result: QueganResult) -> dict[str, float]:
        """'Do no harm': the least-squares calibration matrix W must be an
        exact left-inverse of the forward model A for the estimated
        parameters, i.e. W @ A = I. (Re-deriving u, v, w, z from the
        calibrated data is not a meaningful check here, unlike Ainsworth,
        because calibration collapses HV/VH to a single reciprocal estimate
        and the resulting 4-channel covariance is singular by construction.)
        """
        a_matrix = self.math.system_matrix(result.parameters)
        residual = result.calibration_matrix @ a_matrix - np.eye(3)
        return {
            "left_inverse_residual": float(np.max(np.abs(residual))),
        }
