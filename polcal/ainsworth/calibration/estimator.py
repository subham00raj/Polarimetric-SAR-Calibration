from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter

from polcal.ainsworth.calibration.config import AinsworthConfig
from polcal.ainsworth.calibration.core import AinsworthMath
from polcal.ainsworth.calibration.models import PolSARImage, RangeLineResult
from polcal.ainsworth.calibration.validation import CalibrationValidator


class RangeLineEstimator:
    """Estimates one Ainsworth calibration solution per range line."""

    def __init__(
        self,
        config: AinsworthConfig | None = None,
        math: AinsworthMath | None = None,
        validator: CalibrationValidator | None = None,
    ) -> None:
        self.config = config or AinsworthConfig()
        self.math = math or AinsworthMath(self.config)
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
        ainsworth = self.math.calibrate_covariance_iterative(covariance)
        validation = self.validator.validate(ainsworth)
        return RangeLineResult(row, valid_count, ainsworth, validation)
