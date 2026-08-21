from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter

from polcal.quegan.calibration.config import QueganConfig
from polcal.quegan.calibration.core import QueganMath
from polcal.quegan.calibration.models import PolSARImage, RangeLineResult
from polcal.quegan.calibration.validation import CalibrationValidator


class RangeLineEstimator:
    """Estimates one Quegan cross-talk/phase calibration solution per range line."""

    def __init__(
        self,
        config: QueganConfig | None = None,
        math: QueganMath | None = None,
        validator: CalibrationValidator | None = None,
    ) -> None:
        self.config = config or QueganConfig()
        self.math = math or QueganMath(self.config)
        self.validator = validator or CalibrationValidator(self.config)

    def hh_hv_correlation(self, hh: np.ndarray, hv: np.ndarray) -> np.ndarray:
        window = self.config.correlation_window
        cross = uniform_filter(hh * np.conj(hv), size=window, mode="nearest")
        p_hh = uniform_filter(np.abs(hh) ** 2, size=window, mode="nearest")
        p_hv = uniform_filter(np.abs(hv) ** 2, size=window, mode="nearest")
        denominator = np.sqrt(np.maximum(p_hh * p_hv, self.config.epsilon))
        return np.abs(cross) / denominator

    def estimate(self, image: PolSARImage, row: int) -> RangeLineResult:
        start = max(0, row - self.config.stripe_half_width)
        stop = min(image.rows, row + self.config.stripe_half_width + 1)
        stripe = PolSARImage(
            image.hh[start:stop],
            image.hv[start:stop],
            image.vh[start:stop],
            image.vv[start:stop],
        )

        correlation = self.hh_hv_correlation(stripe.hh, stripe.hv)
        mask = correlation <= self.config.correlation_threshold
        valid_count = int(mask.sum())
        if valid_count < self.config.minimum_valid_pixels:
            raise ValueError(
                f"Too few valid pixels ({valid_count}) for range line {row}."
            )

        covariance = self.math.covariance(
            stripe.hh, stripe.hv, stripe.vh, stripe.vv, mask=mask
        )
        quegan = self.math.solve(covariance)
        validation = self.validator.validate(quegan)
        return RangeLineResult(row, valid_count, quegan, validation)
