from __future__ import annotations

import numpy as np


class ParameterSmoother:
    """Moving-average smoother for complex range-dependent parameters."""

    def __init__(self, window: int = 100) -> None:
        if window <= 0:
            raise ValueError("window must be > 0")
        self.window = window

    def smooth(self, parameter: np.ndarray) -> np.ndarray:
        parameter = np.asarray(parameter, dtype=np.complex128)
        kernel = np.ones(self.window, dtype=np.float64) / self.window
        real = np.convolve(parameter.real, kernel, mode="same")
        imag = np.convolve(parameter.imag, kernel, mode="same")
        return real + 1j * imag

    def smooth_all(
        self,
        u: np.ndarray,
        v: np.ndarray,
        w: np.ndarray,
        z: np.ndarray,
        alpha: np.ndarray,
    ) -> dict[str, np.ndarray]:
        return {
            "u": self.smooth(u),
            "v": self.smooth(v),
            "w": self.smooth(w),
            "z": self.smooth(z),
            "alpha": self.smooth(alpha),
        }


class ComplexProfileInterpolator:
    """Fills failed range-line estimates by independent real/imag interpolation."""

    @staticmethod
    def interpolate(values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=np.complex128).copy()
        good = np.isfinite(values.real) & np.isfinite(values.imag)
        if not np.any(good):
            raise RuntimeError("No valid Ainsworth parameter estimates were obtained.")
        indices = np.arange(values.size)
        real = np.interp(indices, indices[good], values.real[good])
        imag = np.interp(indices, indices[good], values.imag[good])
        return real + 1j * imag
