"""Shared diagnostic plots for Ainsworth/Quegan-style calibration output.

Produces 8 plots:
  1. uncalibrated_hv_vh_power_db.png -- |HV|^2 and |VH|^2 per range line, in
     dB, uncalibrated.
  2. calibrated_hv_vh_power_db.png -- same, calibrated. Comparing 1 and 2
     verifies HV == VH is only true after calibration.
  3. uncalibrated_hv_vs_vh_scatter.png -- |HV| vs |VH| per pixel, uncalibrated
     (scatter against the y=x reciprocity line).
  4. calibrated_hv_vs_vh_scatter.png -- same, calibrated.
  5-8. crosstalk_{u,v,w,z}_db.png -- |u|, |v|, |w|, |z| in dB vs range pixel
     number, matching the style of Figs. 4/5 in Ainsworth et al. (2006).

Reads HH/HV/VH/VV.npy from `data_dir`, calibrated_HH/HV/VH/VV.npy and the
diagnostics .npz from `output_dir`, and writes all plots into `output_dir`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def to_db_power(x: np.ndarray) -> np.ndarray:
    """Power quantity (e.g. |field|^2) -> dB."""
    return 10.0 * np.log10(np.maximum(x, 1e-30))


def to_db_amplitude(x: np.ndarray) -> np.ndarray:
    """Amplitude/ratio quantity (e.g. |u|, |alpha|) -> dB."""
    return 20.0 * np.log10(np.maximum(x, 1e-30))


def generate_diagnostic_plots(
    data_dir: str | Path,
    output_dir: str | Path,
    diagnostics_filename: str,
    *,
    n_sample: int = 200_000,
    seed: int = 0,
) -> None:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading saved calibration outputs...")
    diag = np.load(output_dir / diagnostics_filename)

    HH = np.load(data_dir / "HH.npy", mmap_mode="r")
    HV = np.load(data_dir / "HV.npy", mmap_mode="r")
    VH = np.load(data_dir / "VH.npy", mmap_mode="r")
    VV = np.load(data_dir / "VV.npy", mmap_mode="r")

    cal_HV = np.load(output_dir / "calibrated_HV.npy", mmap_mode="r")
    cal_VH = np.load(output_dir / "calibrated_VH.npy", mmap_mode="r")

    rows = HH.shape[0]
    range_pixels = np.arange(rows)

    # -----------------------------------------------------------------------
    # Plots 1-2: verify HV == VH -- per-range-line mean power, uncal vs cal
    # -----------------------------------------------------------------------

    print("Computing per-range-line HV/VH power (uncalibrated + calibrated)...")

    uncal_hv_power = np.array([np.mean(np.abs(HV[r]) ** 2) for r in range(rows)])
    uncal_vh_power = np.array([np.mean(np.abs(VH[r]) ** 2) for r in range(rows)])
    cal_hv_power = np.array([np.mean(np.abs(cal_HV[r]) ** 2) for r in range(rows)])
    cal_vh_power = np.array([np.mean(np.abs(cal_VH[r]) ** 2) for r in range(rows)])

    for label, hv_power, vh_power, out_name in [
        ("Uncalibrated", uncal_hv_power, uncal_vh_power, "uncalibrated_hv_vh_power_db.png"),
        ("Calibrated", cal_hv_power, cal_vh_power, "calibrated_hv_vh_power_db.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range_pixels, to_db_power(hv_power), color="tab:red", lw=1, label="|HV|^2")
        ax.plot(range_pixels, to_db_power(vh_power), color="tab:blue", lw=1, label="|VH|^2")
        ax.set_xlabel("Range pixel number")
        ax.set_ylabel("Mean power (dB)")
        ax.set_title(f"Reciprocity check ({label}): HV vs VH power per range line")
        ax.legend(loc="best", fontsize=9)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        out_path = output_dir / out_name
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Wrote {out_path}")

    # -----------------------------------------------------------------------
    # Plots 3-4: HV vs VH scatter (per-pixel amplitude), uncal vs cal
    # -----------------------------------------------------------------------

    print("Building HV vs VH scatter plots (subsampled)...")

    rng = np.random.default_rng(seed)
    sample_size = min(n_sample, HV.size)
    flat_idx = rng.choice(HV.size, size=sample_size, replace=False)

    uncal_hv_amp = np.abs(np.asarray(HV).reshape(-1)[flat_idx])
    uncal_vh_amp = np.abs(np.asarray(VH).reshape(-1)[flat_idx])
    cal_hv_amp = np.abs(np.asarray(cal_HV).reshape(-1)[flat_idx])
    cal_vh_amp = np.abs(np.asarray(cal_VH).reshape(-1)[flat_idx])

    for label, hv_amp, vh_amp, out_name in [
        ("Uncalibrated", uncal_hv_amp, uncal_vh_amp, "uncalibrated_hv_vs_vh_scatter.png"),
        ("Calibrated", cal_hv_amp, cal_vh_amp, "calibrated_hv_vs_vh_scatter.png"),
    ]:
        lim = np.percentile(np.concatenate([hv_amp, vh_amp]), 99.5)

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(hv_amp, vh_amp, s=1, alpha=0.05, color="tab:purple", rasterized=True)
        ax.plot([0, lim], [0, lim], color="k", lw=1, ls="--", label="y = x (perfect reciprocity)")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("|HV|")
        ax.set_ylabel("|VH|")
        ax.set_title(f"{label}: |HV| vs |VH| per pixel (n={sample_size:,} sampled)")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_aspect("equal")
        fig.tight_layout()
        out_path = output_dir / out_name
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Wrote {out_path}")

    # -----------------------------------------------------------------------
    # Plots 5-8: |u|, |v|, |w|, |z| in dB vs range pixel number
    # -----------------------------------------------------------------------

    for name in ["u", "v", "w", "z"]:
        param = diag[name]
        param_raw = diag[f"{name}_raw"]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range_pixels, to_db_amplitude(np.abs(param_raw)), color="0.7", lw=0.8, label=f"|{name}| raw (per line)")
        ax.plot(range_pixels, to_db_amplitude(np.abs(param)), color="tab:orange", lw=1.5, label=f"|{name}| smoothed")
        ax.set_xlabel("Range pixel number")
        ax.set_ylabel(f"|{name}| (dB)")
        ax.set_title(f"Crosstalk parameter {name} vs range pixel number")
        ax.legend(loc="best", fontsize=9)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        out_path = output_dir / f"crosstalk_{name}_db.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Wrote {out_path}")

    print("Diagnostic plots complete.")
