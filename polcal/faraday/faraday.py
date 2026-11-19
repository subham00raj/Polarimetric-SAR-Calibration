"""Faraday rotation estimation and correction for quad-pol SAR.

Model (Freeman 2004; Bickel and Bates 1965). The ionosphere rotates the
polarization plane by Omega on the way down and again on the way back, so the
one-way rotation matrix is applied on both sides of the scattering matrix:

    M = F(Omega) . S . F(Omega),   F(Omega) = [[ cos Omega, sin Omega],
                                              [-sin Omega, cos Omega]]

Unlike an orientation-angle rotation (F S F^T), this breaks reciprocity:
M_hv - M_vh = 2 sin(Omega) cos(Omega) (S_hh + S_vv) for a reciprocal target.

Estimator (Bickel and Bates 1965). Transform to the circular basis

    Z = A M A,   A = [[1, j], [j, 1]]

    Z12 = (M_hv - M_vh) + j (M_hh + M_vv)
    Z21 = (M_vh - M_hv) + j (M_hh + M_vv)

and  Omega = -1/4 * arg< Z12 . Z21^* >   (sign matches the F(Omega) above;
verified by injecting known rotations, see main.py self-test).

The estimate is unambiguous for |Omega| < 45 deg. It assumes the system
distortions (cross-talk, channel imbalance) are already removed, so it is best
run on calibrated data; it is also reported on uncalibrated data for reference.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import uniform_filter


def rotation_matrix(omega: float) -> np.ndarray:
    c, s = np.cos(omega), np.sin(omega)
    return np.array([[c, s], [-s, c]])


def apply_faraday(hh, hv, vh, vv, omega):
    """Return F(omega) . M . F(omega) channel-wise (omega scalar or array, radians)."""
    c, s = np.cos(omega), np.sin(omega)
    # F M
    a11 = c * hh + s * vh
    a12 = c * hv + s * vv
    a21 = -s * hh + c * vh
    a22 = -s * hv + c * vv
    # (F M) F
    o_hh = a11 * c - a12 * s
    o_hv = a11 * s + a12 * c
    o_vh = a21 * c - a22 * s
    o_vv = a21 * s + a22 * c
    return o_hh, o_hv, o_vh, o_vv


def correct_faraday(hh, hv, vh, vv, omega):
    """Remove Faraday rotation: S = F(-omega) . M . F(-omega)."""
    return apply_faraday(hh, hv, vh, vv, -np.asarray(omega))


def _boxcar(z: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return z
    return uniform_filter(z.real, window) + 1j * uniform_filter(z.imag, window)


def bickel_bates_product(hh, hv, vh, vv) -> np.ndarray:
    """Per-pixel Z12 . Z21^* (complex128)."""
    hh, hv, vh, vv = (np.asarray(x, dtype=np.complex128) for x in (hh, hv, vh, vv))
    co = 1j * (hh + vv)
    z12 = (hv - vh) + co
    z21 = (vh - hv) + co
    return z12 * np.conj(z21)


@dataclass
class FaradayEstimate:
    omega_scene_deg: float          # from the scene-averaged correlation
    omega_map_deg: np.ndarray       # boxcar-averaged per-pixel estimate
    omega_range_deg: np.ndarray     # one estimate per range column
    window: int

    def summary(self) -> dict:
        m = self.omega_map_deg[np.isfinite(self.omega_map_deg)]
        return {
            "omega_scene_deg": float(self.omega_scene_deg),
            "omega_map_mean_deg": float(m.mean()),
            "omega_map_median_deg": float(np.median(m)),
            "omega_map_std_deg": float(m.std()),
            "omega_map_p05_deg": float(np.percentile(m, 5)),
            "omega_map_p95_deg": float(np.percentile(m, 95)),
            "omega_range_mean_deg": float(np.nanmean(self.omega_range_deg)),
            "omega_range_std_deg": float(np.nanstd(self.omega_range_deg)),
            "window": self.window,
        }


def estimate_faraday(hh, hv, vh, vv, window: int = 15) -> FaradayEstimate:
    """Bickel-Bates Faraday rotation estimate (degrees)."""
    p = bickel_bates_product(hh, hv, vh, vv)
    omega_scene = -0.25 * np.angle(p.mean())
    omega_map = -0.25 * np.angle(_boxcar(p, window))
    omega_range = -0.25 * np.angle(p.mean(axis=0))
    return FaradayEstimate(
        omega_scene_deg=float(np.degrees(omega_scene)),
        omega_map_deg=np.degrees(omega_map).astype(np.float32),
        omega_range_deg=np.degrees(omega_range),
        window=window,
    )
