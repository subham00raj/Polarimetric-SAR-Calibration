from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from polcal.ainsworth.calibration.models import PolSARImage


class SARVisualizer:
    """Visualization-only utilities. They never modify SAR calibration values."""

    @staticmethod
    def _normalize(channel: np.ndarray, percentile: float, gamma: float) -> np.ndarray:
        if not 0 < percentile <= 100:
            raise ValueError("percentile must be in (0, 100].")
        if gamma <= 0:
            raise ValueError("gamma must be > 0.")
        amplitude = np.abs(channel)
        high = np.percentile(amplitude, percentile)
        high = 1.0 if high <= 0 else high
        stretched = np.clip(amplitude / high, 0.0, 1.0) ** gamma
        return (stretched * 255).astype(np.uint8)

    def linear_basis_rgb(
        self,
        image: PolSARImage,
        output_path: str | Path,
        percentile: float = 99.0,
        gamma: float = 0.5,
    ) -> np.ndarray:
        rgb = np.dstack([
            self._normalize(image.hv, percentile, gamma),
            self._normalize(image.hh, percentile, gamma),
            self._normalize(image.vv, percentile, gamma),
        ])
        Image.fromarray(rgb, mode="RGB").save(output_path)
        return rgb

    def grayscale(
        self,
        image: PolSARImage,
        output_path: str | Path,
        percentile: float = 99.0,
        gamma: float = 0.5,
    ) -> np.ndarray:
        span = (
            np.abs(image.hh) ** 2 + np.abs(image.hv) ** 2
            + np.abs(image.vh) ** 2 + np.abs(image.vv) ** 2
        )
        high = np.percentile(span, percentile)
        high = 1.0 if high <= 0 else high
        stretched = np.clip(span / high, 0.0, 1.0) ** gamma
        output = (stretched * 255).astype(np.uint8)
        Image.fromarray(output, mode="L").save(output_path)
        return output
