from __future__ import annotations

import numpy as np
from numpy.linalg import LinAlgError

from polcal.ainsworth.calibration.core import AinsworthMath
from polcal.quegan.calibration.config import QueganConfig
from polcal.quegan.calibration.models import CrosstalkParameters, QueganResult


class QueganMath:
    """Numerical implementation of Quegan (1994), 'A Unified Algorithm for
    Phase and Cross-Talk Calibration of Polarimetric Data'.

    The observed covariance matrix C is indexed in the paper's O =
    (O11, O21, O12, O22) order, which is identical to the UAVSAR paper order
    used by :class:`AinsworthMath` -> (HH, VH, HV, VV). Scattering-vector and
    covariance construction are therefore reused directly from Ainsworth.
    """

    def __init__(self, config: QueganConfig | None = None) -> None:
        self.config = config or QueganConfig()
        self.eps = self.config.epsilon
        self._ainsworth_math = AinsworthMath()

    # -- shared, reused building blocks -------------------------------------------------

    def scattering_vector(
        self, hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray
    ) -> np.ndarray:
        return self._ainsworth_math.scattering_vector(hh, hv, vh, vv)

    def covariance(
        self,
        hh: np.ndarray,
        hv: np.ndarray,
        vh: np.ndarray,
        vv: np.ndarray,
        mask: np.ndarray | None = None,
    ) -> np.ndarray:
        return self._ainsworth_math.covariance(hh, hv, vh, vv, mask=mask)

    @staticmethod
    def hermitian(matrix: np.ndarray) -> np.ndarray:
        return AinsworthMath.hermitian(matrix)

    # -- Quegan cross-talk equations (22)-(30) ------------------------------------------

    def solve_crosstalk(self, covariance: np.ndarray) -> CrosstalkParameters:
        """Solve eqs. (22)-(30) for u, v, w, z and the two (alpha, beta) roots."""
        c = np.asarray(covariance, dtype=np.complex128)
        if c.shape != (4, 4):
            raise ValueError("Covariance matrix must be 4x4.")

        c11, c22, c33, c44 = c[0, 0], c[1, 1], c[2, 2], c[3, 3]
        c14, c41 = c[0, 3], c[3, 0]
        c21, c12 = c[1, 0], c[0, 1]
        c31, c13 = c[2, 0], c[0, 2]
        c24, c42 = c[1, 3], c[3, 1]
        c34, c43 = c[2, 3], c[3, 2]
        c32, c23 = c[2, 1], c[1, 2]

        delta = c11 * c44 - np.abs(c14) ** 2
        if abs(delta) < self.eps:
            raise LinAlgError("Quegan system is singular: Delta ~ 0.")

        u = (c44 * c21 - c41 * c24) / delta
        v = (c11 * c24 - c21 * c14) / delta
        z = (c44 * c31 - c41 * c34) / delta
        w = (c11 * c34 - c31 * c14) / delta

        x = c32 - z * c12 - w * c42  # (27)
        d1 = c22 - u * c12 - v * c42
        d2 = c33 - np.conj(z) * c31 - np.conj(w) * c34

        if abs(x) < self.eps:
            raise LinAlgError("Quegan system is singular: X ~ 0.")
        if abs(d1) < self.eps or abs(d2) < self.eps:
            raise LinAlgError("Quegan system is singular: denominator ~ 0.")

        alpha1 = d1 / x  # (26)
        beta1 = np.abs(x) ** 2 / d1  # (28)
        alpha2 = np.conj(x) / d2  # (29)
        beta2 = d2  # (30)

        if self.config.solution == 1:
            alpha, beta = alpha1, beta1
        else:
            alpha, beta = alpha2, beta2

        return CrosstalkParameters(
            u=u, v=v, w=w, z=z, alpha=alpha, beta=beta,
            alpha1=alpha1, beta1=beta1, alpha2=alpha2, beta2=beta2,
        )

    # -- calibration transform (eq. 41-42, Y = 1, k = 1) --------------------------------

    def system_matrix(self, params: CrosstalkParameters) -> np.ndarray:
        """Build the noiseless system matrix of eq. (41) with Y = k = 1.

        Absolute gain Y and the receive/transmit channel-imbalance ratio k
        cannot be recovered from distributed-target statistics alone (per
        Section IV of the paper); they are fixed to 1 so the recovered
        S = (S11, S21, S22) is calibrated up to that unresolved scale.
        """
        u, v, w, z, alpha = params.u, params.v, params.w, params.z, params.alpha
        return np.array(
            [
                [alpha, v + alpha * w, v * w],
                [alpha * u, alpha, v],
                [alpha * z, 1, w],
                [alpha * u * z, u + alpha * z, 1],
            ],
            dtype=np.complex128,
        )

    def calibration_matrix(self, params: CrosstalkParameters) -> np.ndarray:
        """Least-squares calibration transform W = (A^H A)^-1 A^H (eq. 42)."""
        a = self.system_matrix(params)
        gram = a.conj().T @ a
        try:
            inverse_gram = np.linalg.inv(gram)
        except np.linalg.LinAlgError as exc:
            raise LinAlgError("Quegan calibration matrix A^H A is singular.") from exc
        return inverse_gram @ a.conj().T

    def calibrate_covariance(
        self, covariance: np.ndarray, params: CrosstalkParameters
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply the calibration transform to a covariance matrix.

        Returns the 4x4 observation-order covariance reconstructed from the
        calibrated 3-vector (S11, S21, S22), with the reciprocal cross-pol
        channel duplicated per the reciprocity assumption (Section II.A.2).
        """
        w_matrix = self.calibration_matrix(params)
        calibrated_3 = self.hermitian(w_matrix @ covariance @ w_matrix.conj().T)
        calibrated_4 = np.array(
            [
                [calibrated_3[0, 0], calibrated_3[0, 1], calibrated_3[0, 1], calibrated_3[0, 2]],
                [calibrated_3[1, 0], calibrated_3[1, 1], calibrated_3[1, 1], calibrated_3[1, 2]],
                [calibrated_3[1, 0], calibrated_3[1, 1], calibrated_3[1, 1], calibrated_3[1, 2]],
                [calibrated_3[2, 0], calibrated_3[2, 1], calibrated_3[2, 1], calibrated_3[2, 2]],
            ],
            dtype=np.complex128,
        )
        return calibrated_3, self.hermitian(calibrated_4)

    def solve(self, covariance: np.ndarray) -> QueganResult:
        params = self.solve_crosstalk(covariance)
        w_matrix = self.calibration_matrix(params)
        _, calibrated_covariance = self.calibrate_covariance(covariance, params)
        return QueganResult(
            parameters=params,
            calibration_matrix=w_matrix,
            calibrated_covariance=calibrated_covariance,
        )

    def apply_matrix_to_row(
        self,
        hh: np.ndarray,
        hv: np.ndarray,
        vh: np.ndarray,
        vv: np.ndarray,
        calibration_matrix: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Apply W to every pixel's observation vector O = (HH, VH, HV, VV).

        Returns calibrated (hh, hv, vh, vv); hv and vh are identical, since
        Quegan's model recovers a single reciprocal cross-pol estimate S21.
        """
        observation = np.vstack([hh, vh, hv, vv])
        calibrated = calibration_matrix @ observation
        cross = calibrated[1]
        return calibrated[0], cross, cross, calibrated[2]
