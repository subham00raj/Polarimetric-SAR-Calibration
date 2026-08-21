from __future__ import annotations
import numpy as np
from numpy.linalg import LinAlgError
from polcal.ainsworth.calibration.config import AinsworthConfig
from polcal.ainsworth.calibration.models import (
    AinsworthResult,
    CrosstalkParameters,
    IterationRecord,
)

class AinsworthMath:
    """Numerical implementation of the equations used by the Ainsworth method."""

    def __init__(self, config: AinsworthConfig | None = None) -> None:
        self.config = config or AinsworthConfig()
        self.eps = self.config.epsilon

    @staticmethod
    def scattering_vector(
        hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray
    ) -> np.ndarray:
        """Return UAVSAR paper order: [HH, VH, HV, VV]^T."""
        return np.stack([hh, vh, hv, vv], axis=0).astype(np.complex128)

    def covariance(
        self,
        hh: np.ndarray,
        hv: np.ndarray,
        vh: np.ndarray,
        vv: np.ndarray,
        mask: np.ndarray | None = None,
    ) -> np.ndarray:
        scattering = self.scattering_vector(hh, hv, vh, vv).reshape(4, -1)
        if mask is not None:
            mask = np.asarray(mask, dtype=bool).reshape(-1)
            if mask.size != scattering.shape[1]:
                raise ValueError("Covariance mask has an incompatible size.")
            scattering = scattering[:, mask]
        if scattering.shape[1] == 0:
            raise ValueError("No valid pixels available for covariance estimation.")
        covariance = (scattering @ scattering.conj().T) / scattering.shape[1]
        return self.hermitian(covariance)

    @staticmethod
    def hermitian(matrix: np.ndarray) -> np.ndarray:
        return 0.5 * (matrix + matrix.conj().T)

    def alpha(self, covariance: np.ndarray) -> complex:
        c22 = covariance[1, 1]
        c33 = covariance[2, 2]
        c23 = covariance[1, 2]
        if abs(c22) < self.eps or abs(c33) < self.eps:
            raise ValueError("C22 or C33 is too small to estimate alpha.")
        phase = 1.0 + 0.0j if abs(c23) < self.eps else c23 / abs(c23)
        amplitude = np.sqrt(abs(c22 / c33))
        return phase * amplitude

    @staticmethod
    def A(covariance: np.ndarray) -> complex:
        return 0.5 * (covariance[2, 0] + covariance[1, 0])

    @staticmethod
    def B(covariance: np.ndarray) -> complex:
        return 0.5 * (covariance[2, 3] + covariance[1, 3])

    @staticmethod
    def zeta(covariance: np.ndarray) -> np.ndarray:
        return np.array(
            [
                [0, 0, covariance[3, 0], covariance[0, 0]],
                [covariance[0, 0], covariance[3, 0], 0, 0],
                [0, 0, covariance[3, 3], covariance[0, 3]],
                [covariance[0, 3], covariance[3, 3], 0, 0],
            ],
            dtype=np.complex128,
        )

    @staticmethod
    def tau(covariance: np.ndarray) -> np.ndarray:
        return np.array(
            [
                [0, covariance[2, 2], covariance[2, 1], 0],
                [0, covariance[1, 2], covariance[1, 1], 0],
                [covariance[2, 2], 0, 0, covariance[2, 1]],
                [covariance[1, 2], 0, 0, covariance[1, 1]],
            ],
            dtype=np.complex128,
        )

    @staticmethod
    def X(covariance: np.ndarray, A: complex, B: complex) -> np.ndarray:
        return np.array(
            [
                covariance[2, 0] - A,
                covariance[1, 0] - A,
                covariance[2, 3] - B,
                covariance[1, 3] - B,
            ],
            dtype=np.complex128,
        )

    def parameter_updates(
        self, covariance: np.ndarray, A: complex, B: complex
    ) -> tuple[complex, complex, complex, complex]:
        zeta = self.zeta(covariance)
        tau = self.tau(covariance)
        X = self.X(covariance, A, B)
        matrix = np.block(
            [
                [np.real(zeta + tau), -np.imag(zeta - tau)],
                [np.imag(zeta + tau), np.real(zeta - tau)],
            ]
        )
        rhs = np.concatenate([np.real(X), np.imag(X)])
        try:
            solution = np.linalg.solve(matrix, rhs)
        except np.linalg.LinAlgError as exc:
            raise LinAlgError("Ainsworth 8x8 system is singular.") from exc
        return tuple(solution[i] + 1j * solution[i + 4] for i in range(4))  # type: ignore[return-value]

    def sigma(self, parameters: CrosstalkParameters) -> np.ndarray:
        u, v, w, z, alpha = (
            parameters.u,
            parameters.v,
            parameters.w,
            parameters.z,
            parameters.alpha,
        )
        sqrt_alpha = np.sqrt(alpha)
        denominator = (u * w - 1.0) * (v * z - 1.0)
        if abs(denominator) < self.eps:
            raise LinAlgError("Ainsworth calibration matrix is singular.")
        sigma = np.array(
            [
                [1, -w, -v, v * w],
                [-u / sqrt_alpha, 1 / sqrt_alpha, u * v / sqrt_alpha, -v / sqrt_alpha],
                [-z * sqrt_alpha, w * z * sqrt_alpha, sqrt_alpha, -w * sqrt_alpha],
                [u * z, -z, -u, 1],
            ],
            dtype=np.complex128,
        )
        return sigma / denominator

    def calibrate_covariance(
        self, covariance: np.ndarray, sigma: np.ndarray
    ) -> np.ndarray:
        return self.hermitian(sigma @ covariance @ sigma.conj().T)

    def calibrate_covariance_iterative(self, covariance: np.ndarray) -> AinsworthResult:
        covariance = np.asarray(covariance, dtype=np.complex128)
        if covariance.shape != (4, 4):
            raise ValueError("C0 must be 4x4.")
        covariance = self.hermitian(covariance)

        params = CrosstalkParameters(0j, 0j, 0j, 0j, self.alpha(covariance))
        gamma = 100.0
        history: list[IterationRecord] = []

        for iteration in range(1, self.config.max_iterations + 1):
            sigma_i = self.sigma(params)
            corrected = self.calibrate_covariance(covariance, sigma_i)
            A = self.A(corrected)
            B = self.B(corrected)
            du, dv, dw, dz = self.parameter_updates(corrected, A, B)
            alpha_i = self.alpha(corrected)

            sqrt_alpha = np.sqrt(params.alpha)
            params = CrosstalkParameters(
                u=params.u + du / sqrt_alpha,
                v=params.v + dv / sqrt_alpha,
                w=params.w + dw / sqrt_alpha,
                z=params.z + dz / sqrt_alpha,
                alpha=params.alpha * alpha_i,
            )
            gamma = max(abs(du), abs(dv), abs(dw), abs(dz))
            history.append(
                IterationRecord(
                    iteration, du, dv, dw, dz,
                    params.u, params.v, params.w, params.z, params.alpha, gamma,
                )
            )
            if gamma <= self.config.tolerance:
                break

        sigma = self.sigma(params)
        calibrated = self.calibrate_covariance(covariance, sigma)
        return AinsworthResult(
            parameters=params,
            sigma=sigma,
            calibrated_covariance=calibrated,
            iterations=iteration,
            gamma=gamma,
            converged=gamma <= self.config.tolerance,
            history=history,
        )

    def apply_sigma_to_row(
        self,
        hh: np.ndarray,
        hv: np.ndarray,
        vh: np.ndarray,
        vv: np.ndarray,
        sigma: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        observation = np.vstack([hh, vh, hv, vv])
        calibrated = sigma @ observation
        return calibrated[0], calibrated[2], calibrated[1], calibrated[3]
