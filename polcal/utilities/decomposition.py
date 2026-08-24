"""Polarimetric target decompositions for quad-pol scattering-matrix data.

Implements:
  - Pauli decomposition: a direct, per-pixel basis change of the scattering
    matrix into odd-bounce, double-bounce, and volume/cross-pol components.
  - Yamaguchi four-component scattering power decomposition (Yamaguchi et
    al., 2005, "Four-component scattering model for polarimetric SAR image
    decomposition," IEEE TGRS 43(8)): a model-based decomposition of the
    (locally averaged) covariance matrix into surface, double-bounce,
    volume, and helix scattering powers.

Both operate on the four linear-polarization channels (HH, HV, VH, VV) in
the user-facing channel order used throughout ``polcal``.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter

SQRT2 = np.sqrt(2.0)


def _boxcar_complex(x: np.ndarray, window: int) -> np.ndarray:
    real = uniform_filter(x.real, size=window, mode="reflect")
    imag = uniform_filter(x.imag, size=window, mode="reflect")
    return real + 1j * imag


def _boxcar_real(x: np.ndarray, window: int) -> np.ndarray:
    return uniform_filter(x, size=window, mode="reflect")


def _normalize_channel(channel: np.ndarray, percentile: float, gamma: float) -> np.ndarray:
    high = np.percentile(channel, percentile)
    high = 1.0 if high <= 0 else high
    return np.clip(channel / high, 0.0, 1.0) ** gamma


def _rgb_from_powers(r: np.ndarray, g: np.ndarray, b: np.ndarray,
                      percentile: float, gamma: float) -> np.ndarray:
    stacked = np.dstack([
        _normalize_channel(r, percentile, gamma),
        _normalize_channel(g, percentile, gamma),
        _normalize_channel(b, percentile, gamma),
    ])
    return (stacked * 255).astype(np.uint8)


def pauli_components(hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray):
    """Per-pixel Pauli-basis scattering amplitudes.

    Returns (double_bounce, volume, surface) = (|HH-VV|, |HV+VH|/sqrt(2), |HH+VV|),
    the standard odd-bounce/double-bounce/volume decomposition of the
    scattering matrix under reflection symmetry (Cloude & Pottier, 1996).
    """
    double_bounce = np.abs(hh - vv)
    volume = np.abs(hv + vh) / SQRT2
    surface = np.abs(hh + vv)
    return double_bounce, volume, surface


def pauli_rgb(hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray,
              *, percentile: float = 99.0, gamma: float = 0.5) -> np.ndarray:
    """Pauli RGB composite: R = |HH-VV| (double-bounce), G = |HV+VH|/sqrt(2)
    (volume/cross-pol), B = |HH+VV| (surface)."""
    double_bounce, volume, surface = pauli_components(hh, hv, vh, vv)
    return _rgb_from_powers(double_bounce, volume, surface, percentile, gamma)


def yamaguchi_four_component(
    hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray, *, window: int = 5
):
    """Yamaguchi et al. (2005) four-component scattering power decomposition.

    The scattering vector is taken in the reciprocal Pauli-like lexicographic
    basis k = [HH, sqrt(2)*HV_avg, VV], with HV_avg = (HV+VH)/2. The
    covariance matrix elements are estimated with a boxcar average of size
    ``window`` (required by the model; a single pixel's covariance matrix
    has rank 1 and cannot be decomposed). Returns the surface (Ps),
    double-bounce (Pd), volume (Pv), and helix (Pc) scattering power maps,
    each with the same shape as the input channels.
    """
    hv_avg = 0.5 * (hv + vh)

    c11 = _boxcar_real(np.abs(hh) ** 2, window)
    c33 = _boxcar_real(np.abs(vv) ** 2, window)
    c22 = 2.0 * _boxcar_real(np.abs(hv_avg) ** 2, window)
    c13 = _boxcar_complex(hh * np.conj(vv), window)
    c12 = SQRT2 * _boxcar_complex(hh * np.conj(hv_avg), window)
    c23 = SQRT2 * _boxcar_complex(hv_avg * np.conj(vv), window)

    span = c11 + c22 + c33

    # Helix scattering power: Pc = 2|Im(<(HH-VV) HV*>)| = sqrt(2)|Im(C12)+Im(C23)|.
    pc = SQRT2 * np.abs(c12.imag + c23.imag)

    # Volume scattering power, from a canonical random-dipole-cloud model
    # with power ratio <HH.HH*>:<HV.HV*>:<VV.VV*> = 8:3:8, i.e. Pv = 8*<|Shv|^2>/3
    # = 4*C22/3 (Yamaguchi et al., 2005, Eq. 15-16).
    pv = 4.0 * c22 / 3.0

    # The same canonical model predicts a real correlation rho = <Shh Svv*>/<|Shv|^2>
    # of +1 (HH-dominant branch) or -1 (VV-dominant branch); its contribution
    # to C13 is removed before the Freeman-Durden-style surface/double-bounce
    # split on the residual (helix- and volume-free) covariance.
    hh_stronger = c11 >= c33
    rho = np.where(hh_stronger, 1.0, -1.0)
    c13_res = c13 - rho * (pv / 4.0)
    c11_res = np.maximum(c11 - pv / 4.0, 0.0)
    c33_res = np.maximum(c33 - pv / 4.0, 0.0)

    # Freeman-Durden two-component split of the residual (helix- and
    # volume-free) covariance into a surface term fs*[[1,beta],[beta*,|beta|^2]]
    # and a double-bounce term fd*[[|alpha|^2,alpha],[alpha*,1]].
    #
    # Surface-dominant branch (Re(C13_res) >= 0): fix the double-bounce
    # ratio alpha = -1 (canonical dielectric-ground/vertical-structure
    # value) and solve the resulting system for fs, fd, and beta:
    #   fs = |C13_res + C11_res|^2 / [2*Re(C13_res + C11_res) + C33_res - C11_res]
    #   fd = C11_res - fs
    #   beta = (C13_res + C11_res)/fs - 1
    #   Ps = fs*(1+|beta|^2), Pd = fd*(1+|alpha|^2) = 2*fd
    #
    # Double-bounce-dominant branch (Re(C13_res) < 0): fix the surface
    # ratio beta = +1 (canonical flat-surface value) and solve symmetrically:
    #   fd = |C13_res - C33_res|^2 / [C11_res - C33_res - 2*Re(C13_res - C33_res)]
    #   fs = C33_res - fd
    #   alpha = (C13_res - C33_res)/fd + 1
    #   Pd = fd*(1+|alpha|^2), Ps = fs*(1+|beta|^2) = 2*fs
    surface_dominant = c13_res.real >= 0

    with np.errstate(divide="ignore", invalid="ignore"):
        num_s = c13_res + c11_res
        den_s = 2 * num_s.real + c33_res - c11_res
        fs = np.divide(np.abs(num_s) ** 2, den_s, out=np.zeros_like(c11_res), where=den_s != 0)
        fd_from_s = np.maximum(c11_res - fs, 0.0)
        beta = np.divide(num_s, fs, out=np.ones_like(c13_res), where=fs > 0) - 1
        ps_from_s = fs * (1 + np.abs(beta) ** 2)
        pd_from_s = fd_from_s * 2.0  # |alpha|^2 = 1

        num_d = c13_res - c33_res
        den_d = c11_res - c33_res - 2 * num_d.real
        fd = np.divide(np.abs(num_d) ** 2, den_d, out=np.zeros_like(c33_res), where=den_d != 0)
        fs_from_d = np.maximum(c33_res - fd, 0.0)
        alpha = np.divide(num_d, fd, out=-np.ones_like(c13_res), where=fd > 0) + 1
        pd_from_d = fd * (1 + np.abs(alpha) ** 2)
        ps_from_d = fs_from_d * 2.0  # |beta|^2 = 1

    ps = np.where(surface_dominant, ps_from_s, ps_from_d)
    pd = np.where(surface_dominant, pd_from_s, pd_from_d)

    ps = np.nan_to_num(np.maximum(ps, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
    pd = np.nan_to_num(np.maximum(pd, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
    pv = np.nan_to_num(np.maximum(pv, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
    pc = np.nan_to_num(np.maximum(pc, 0.0), nan=0.0, posinf=0.0, neginf=0.0)

    # Renormalize so Ps+Pd+Pv+Pc reproduces the total span exactly (the
    # piecewise closed-form split above can leave small numerical slack).
    total = ps + pd + pv + pc
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.divide(span, total, out=np.ones_like(span), where=total > 0)
    return ps * scale, pd * scale, pv * scale, pc * scale


def yamaguchi_rgb(hh: np.ndarray, hv: np.ndarray, vh: np.ndarray, vv: np.ndarray,
                   *, window: int = 5, percentile: float = 99.0, gamma: float = 0.5) -> np.ndarray:
    """Yamaguchi four-component RGB composite: R = Pd, G = Pv, B = Ps."""
    ps, pd, pv, _pc = yamaguchi_four_component(hh, hv, vh, vv, window=window)
    return _rgb_from_powers(pd, pv, ps, percentile, gamma)
