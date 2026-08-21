from __future__ import annotations

from pathlib import Path

import numpy as np
from tqdm import tqdm
from numpy.linalg import LinAlgError

from polcal.ainsworth.calibration.config import AinsworthConfig
from polcal.ainsworth.calibration.core import AinsworthMath
from polcal.ainsworth.calibration.estimator import RangeLineEstimator
from polcal.ainsworth.calibration.models import CalibrationDiagnostics, PolSARImage
from polcal.ainsworth.calibration.smoothing import ComplexProfileInterpolator, ParameterSmoother


class AinsworthCalibrator:
    """Production-facing orchestration layer for complete-image calibration."""

    def __init__(
        self,
        config: AinsworthConfig | None = None,
        *,
        range_estimator: RangeLineEstimator | None = None,
    ) -> None:
        self.config = config or AinsworthConfig()
        self.math = AinsworthMath(self.config)
        self.estimator = range_estimator or RangeLineEstimator(self.config, self.math)
        self.smoother = ParameterSmoother(self.config.smoothing_window)
        self.interpolator = ComplexProfileInterpolator()

    def _estimate_profiles(
        self, image: PolSARImage, show_progress: bool
    ) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray | None]]:
        rows = image.rows
        complex_nan = lambda: np.full(rows, np.nan + 0j, dtype=np.complex128)
        profiles = {name: complex_nan() for name in ("u", "v", "w", "z", "alpha")}
        gamma = np.full(rows, np.nan)
        iterations = np.zeros(rows, dtype=np.int32)
        valid_pixels = np.zeros(rows, dtype=np.int64)
        converged = np.zeros(rows, dtype=bool)
        validation_passed = np.zeros(rows, dtype=bool)
        sigma_raw: list[np.ndarray | None] = [None] * rows

        iterator = range(rows)
        if show_progress:
            iterator = tqdm(iterator, desc="Estimating Ainsworth parameters", unit="range")

        for row in iterator:
            try:
                result = self.estimator.estimate(image, row)
            except (ValueError, LinAlgError, FloatingPointError):
                continue

            p = result.ainsworth.parameters
            profiles["u"][row] = p.u
            profiles["v"][row] = p.v
            profiles["w"][row] = p.w
            profiles["z"][row] = p.z
            profiles["alpha"][row] = p.alpha
            gamma[row] = result.ainsworth.gamma
            iterations[row] = result.ainsworth.iterations
            valid_pixels[row] = result.valid_count
            converged[row] = result.ainsworth.converged
            validation_passed[row] = result.validation.passed
            sigma_raw[row] = result.ainsworth.sigma

        return profiles, gamma, iterations, valid_pixels, converged, validation_passed, sigma_raw

    def calibrate(
        self, 
        image: PolSARImage, 
        *, 
        show_progress: bool = True
    ) -> tuple[PolSARImage, CalibrationDiagnostics]:
        
        profiles, gamma, iterations, valid_pixels, converged, validation_passed, sigma_raw = self._estimate_profiles(
            image, show_progress
        )

        raw = {name: self.interpolator.interpolate(values) for name, values in profiles.items()}
        smoothed = self.smoother.smooth_all(
            raw["u"], raw["v"], raw["w"], raw["z"], raw["alpha"]
        )
        smoothed["alpha"][np.abs(smoothed["alpha"]) < self.config.epsilon] = 1.0 + 0j

        calibrated = self._apply_profiles(image, smoothed, show_progress)
        diagnostics = CalibrationDiagnostics(
            u_raw=raw["u"], v_raw=raw["v"], w_raw=raw["w"], z_raw=raw["z"], alpha_raw=raw["alpha"],
            u=smoothed["u"], v=smoothed["v"], w=smoothed["w"], z=smoothed["z"], alpha=smoothed["alpha"],
            gamma=gamma, iterations=iterations, valid_pixels=valid_pixels,
            converged=converged, validation_passed=validation_passed,
            sigma=self._build_sigma_profile(smoothed), config=self.config,
        )
        return calibrated, diagnostics

    def _build_sigma_profile(self, profiles: dict[str, np.ndarray]) -> list[np.ndarray | None]:
        sigma_profile: list[np.ndarray | None] = []
        for row in range(len(profiles["u"])):
            try:
                from .models import CrosstalkParameters
                sigma_profile.append(
                    self.math.sigma(CrosstalkParameters(
                        profiles["u"][row], profiles["v"][row], profiles["w"][row],
                        profiles["z"][row], profiles["alpha"][row]
                    ))
                )
            except LinAlgError:
                sigma_profile.append(None)
        return sigma_profile

    def _apply_profiles(
        self, image: PolSARImage, profiles: dict[str, np.ndarray], show_progress: bool
    ) -> PolSARImage:
        calibrated = [np.empty_like(image.hh) for _ in range(4)]
        iterator = range(image.rows)
        if show_progress:
            iterator = tqdm(iterator, desc="Applying Ainsworth calibration", unit="range")

        for row in iterator:
            try:
                from .models import CrosstalkParameters
                sigma = self.math.sigma(CrosstalkParameters(
                    profiles["u"][row], profiles["v"][row], profiles["w"][row],
                    profiles["z"][row], profiles["alpha"][row]
                ))
            except LinAlgError:
                calibrated[0][row] = image.hh[row]
                calibrated[1][row] = image.hv[row]
                calibrated[2][row] = image.vh[row]
                calibrated[3][row] = image.vv[row]
                continue

            calibrated[0][row], calibrated[1][row], calibrated[2][row], calibrated[3][row] = self.math.apply_sigma_to_row(
                image.hh[row], image.hv[row], image.vh[row], image.vv[row], sigma
            )
        return PolSARImage(*calibrated)


class DiagnosticStore:
    """Persistence for calibration profiles and diagnostic arrays."""

    @staticmethod
    def save(diagnostics: CalibrationDiagnostics, path: str | Path) -> None:
        data = diagnostics.as_dict()
        # sigma contains Python objects and is deliberately not serialized here.
        data.pop("sigma", None)
        np.savez(path, **data)
