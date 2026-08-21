from __future__ import annotations

from pathlib import Path

import numpy as np
from tqdm import tqdm
from numpy.linalg import LinAlgError

from polcal.quegan.calibration.config import QueganConfig
from polcal.quegan.calibration.core import QueganMath
from polcal.quegan.calibration.estimator import RangeLineEstimator
from polcal.quegan.calibration.models import CalibrationDiagnostics, CrosstalkParameters, PolSARImage
from polcal.quegan.calibration.smoothing import ComplexProfileInterpolator, ParameterSmoother


class QueganCalibrator:
    """Production-facing orchestration layer for complete-image calibration."""

    def __init__(
        self,
        config: QueganConfig | None = None,
        *,
        range_estimator: RangeLineEstimator | None = None,
    ) -> None:
        self.config = config or QueganConfig()
        self.math = QueganMath(self.config)
        self.estimator = range_estimator or RangeLineEstimator(self.config, self.math)
        self.smoother = ParameterSmoother(self.config.smoothing_window)
        self.interpolator = ComplexProfileInterpolator()

    def _estimate_profiles(
        self, image: PolSARImage, show_progress: bool
    ) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray, np.ndarray]:
        rows = image.rows
        complex_nan = lambda: np.full(rows, np.nan + 0j, dtype=np.complex128)
        profiles = {
            name: complex_nan()
            for name in ("u", "v", "w", "z", "alpha", "beta", "alpha1", "alpha2")
        }
        valid_pixels = np.zeros(rows, dtype=np.int64)
        validation_passed = np.zeros(rows, dtype=bool)

        iterator = range(rows)
        if show_progress:
            iterator = tqdm(iterator, desc="Estimating Quegan parameters", unit="range")

        for row in iterator:
            try:
                result = self.estimator.estimate(image, row)
            except (ValueError, LinAlgError, FloatingPointError):
                continue

            p = result.quegan.parameters
            profiles["u"][row] = p.u
            profiles["v"][row] = p.v
            profiles["w"][row] = p.w
            profiles["z"][row] = p.z
            profiles["alpha"][row] = p.alpha
            profiles["beta"][row] = p.beta
            profiles["alpha1"][row] = p.alpha1
            profiles["alpha2"][row] = p.alpha2
            valid_pixels[row] = result.valid_count
            validation_passed[row] = result.validation.passed

        return profiles, valid_pixels, validation_passed

    def calibrate(
        self,
        image: PolSARImage,
        *,
        show_progress: bool = True,
    ) -> tuple[PolSARImage, CalibrationDiagnostics]:

        profiles, valid_pixels, validation_passed = self._estimate_profiles(image, show_progress)

        raw = {name: self.interpolator.interpolate(values) for name, values in profiles.items()}
        smoothed = self.smoother.smooth_all(
            raw["u"], raw["v"], raw["w"], raw["z"], raw["alpha"]
        )
        smoothed["beta"] = self.smoother.smooth(raw["beta"])
        smoothed["alpha"][np.abs(smoothed["alpha"]) < self.config.epsilon] = 1.0 + 0j

        calibrated, calibration_matrix = self._apply_profiles(image, smoothed, show_progress)
        diagnostics = CalibrationDiagnostics(
            u_raw=raw["u"], v_raw=raw["v"], w_raw=raw["w"], z_raw=raw["z"],
            alpha_raw=raw["alpha"], beta_raw=raw["beta"],
            u=smoothed["u"], v=smoothed["v"], w=smoothed["w"], z=smoothed["z"],
            alpha=smoothed["alpha"], beta=smoothed["beta"],
            alpha1=raw["alpha1"], alpha2=raw["alpha2"],
            valid_pixels=valid_pixels, validation_passed=validation_passed,
            calibration_matrix=calibration_matrix, config=self.config,
        )
        return calibrated, diagnostics

    def _row_parameters(self, profiles: dict[str, np.ndarray], row: int) -> CrosstalkParameters:
        return CrosstalkParameters(
            u=profiles["u"][row], v=profiles["v"][row], w=profiles["w"][row],
            z=profiles["z"][row], alpha=profiles["alpha"][row], beta=profiles["beta"][row],
            alpha1=profiles["alpha"][row], beta1=profiles["beta"][row],
            alpha2=profiles["alpha"][row], beta2=profiles["beta"][row],
        )

    def _apply_profiles(
        self, image: PolSARImage, profiles: dict[str, np.ndarray], show_progress: bool
    ) -> tuple[PolSARImage, list[np.ndarray | None]]:
        calibrated = [np.empty_like(image.hh) for _ in range(4)]
        calibration_matrix: list[np.ndarray | None] = [None] * image.rows
        iterator = range(image.rows)
        if show_progress:
            iterator = tqdm(iterator, desc="Applying Quegan calibration", unit="range")

        for row in iterator:
            try:
                params = self._row_parameters(profiles, row)
                w_matrix = self.math.calibration_matrix(params)
            except LinAlgError:
                calibrated[0][row] = image.hh[row]
                calibrated[1][row] = image.hv[row]
                calibrated[2][row] = image.vh[row]
                calibrated[3][row] = image.vv[row]
                continue

            calibration_matrix[row] = w_matrix
            calibrated[0][row], calibrated[1][row], calibrated[2][row], calibrated[3][row] = (
                self.math.apply_matrix_to_row(
                    image.hh[row], image.hv[row], image.vh[row], image.vv[row], w_matrix
                )
            )
        return PolSARImage(*calibrated), calibration_matrix


class DiagnosticStore:
    """Persistence for calibration profiles and diagnostic arrays."""

    @staticmethod
    def save(diagnostics: CalibrationDiagnostics, path: str | Path) -> None:
        data = diagnostics.as_dict()
        np.savez(path, **data)
