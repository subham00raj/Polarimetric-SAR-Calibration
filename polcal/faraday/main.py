"""Faraday rotation estimation and correction for a quad-pol scene.

Input : uncalibrated HH, HV, VH, VV complex arrays (.npy) in one folder.
Output: Faraday-corrected ("calibrated") channels, a JSON summary, a figure,
        and a before/after report printed to the terminal.

Run:
    uv run python -m polcal.faraday.main                      # uses data/
    uv run python -m polcal.faraday.main --input path/to/dir --output out/
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from polcal.faraday import apply_faraday, correct_faraday, estimate_faraday
from polcal.faraday.faraday import DEFAULT_WINDOW

CHANNELS = ("HH", "HV", "VH", "VV")
ROOT = Path(__file__).resolve().parents[2]


def load(directory: Path) -> tuple[np.ndarray, ...]:
    missing = [c for c in CHANNELS if not (directory / f"{c}.npy").exists()]
    if missing:
        raise FileNotFoundError(f"{directory} is missing {', '.join(m + '.npy' for m in missing)}")
    return tuple(np.load(directory / f"{c}.npy").astype(np.complex64) for c in CHANNELS)


def hv_vh_mismatch_db(img) -> float:
    """Non-reciprocity 10 log10( <|HV - VH|^2> / <(|HV|^2 + |VH|^2) / 2> ); lower is better."""
    hv, vh = img[1], img[2]
    num = np.mean(np.abs(hv - vh) ** 2)
    den = np.mean((np.abs(hv) ** 2 + np.abs(vh) ** 2) / 2)
    return float(10 * np.log10(num / den))


def channel_change(before, after) -> dict:
    out = {}
    for name, b, a in zip(CHANNELS, before, after):
        pb, pa = np.abs(b) ** 2, np.abs(a) ** 2
        out[name] = {
            "mean_power_change_pct": float(100 * (pa.mean() - pb.mean()) / pb.mean()),
            "median_abs_amplitude_change_pct": float(
                100 * np.median(np.abs(np.abs(a) - np.abs(b)) / (np.abs(b) + 1e-12))),
        }
    return out


def print_report(before: dict, after: dict, change: dict, selftest: list, window: int) -> None:
    rows = [
        ("Scene Omega (deg)", "omega_scene_deg", "{:+.3f}"),
        ("Map median (deg)", "omega_map_median_deg", "{:+.3f}"),
        ("Map std (deg)", "omega_map_std_deg", "{:.3f}"),
        ("Map 5th pct (deg)", "omega_map_p05_deg", "{:+.3f}"),
        ("Map 95th pct (deg)", "omega_map_p95_deg", "{:+.3f}"),
        ("Range-profile std (deg)", "omega_range_std_deg", "{:.3f}"),
        ("HV-VH mismatch (dB)", "hv_vh_mismatch_db", "{:+.2f}"),
    ]
    w0, w = 30, 16
    line = "=" * (w0 + 2 * w)
    print("\n" + line)
    print("FARADAY ROTATION REPORT")
    print(f"Estimator: Meyer & Nicoll (2008) eqs. 13-15, {window}x{window} boxcar")
    print(line)
    print(f"{'':{w0}s}{'Uncalibrated':>{w}s}{'Calibrated':>{w}s}")
    print("-" * len(line))
    for label, key, fmt in rows:
        print(f"{label:{w0}s}{fmt.format(before[key]):>{w}s}{fmt.format(after[key]):>{w}s}")
    ok = lambda s: "yes" if abs(s["omega_scene_deg"]) < 5 else "NO"
    print(f"{'|Omega| < 5 deg (acceptable)':{w0}s}{ok(before):>{w}s}{ok(after):>{w}s}")
    print("-" * len(line))
    print(f"Correction applied: Omega = {before['omega_scene_deg']:+.3f} deg "
          f"-> residual {after['omega_scene_deg']:+.4f} deg")
    print("Change per channel (calibrated vs uncalibrated):")
    for c in CHANNELS:
        m = change[c]
        print(f"  {c}: mean power {m['mean_power_change_pct']:+.4f}% | "
              f"median |amplitude| {m['median_abs_amplitude_change_pct']:.4f}%")
    ok_test = all(abs(t["recovered_deg"] - t["injected_deg"]) < 0.01 for t in selftest)
    print(f"Self-test (inject 1-20 deg, recover): {'PASS' if ok_test else 'FAIL'}")
    print("Note: on data not yet corrected for cross-talk, part of Omega can be apparent rotation\n"
          "      caused by cross-talk (Meyer & Nicoll 2008, Sec. II-C2).")
    print(line)


def make_figure(est_before, est_after, selftest, path: Path) -> None:
    fig, ax = plt.subplots(1, 4, figsize=(22, 4.8))
    for a, est, title in ((ax[0], est_before, "Uncalibrated"), (ax[1], est_after, "Calibrated")):
        im = a.imshow(est.omega_map_deg, cmap="RdBu_r", vmin=-5, vmax=5)
        a.set_title(f"Ω map, {title} ({est.window}×{est.window} boxcar)")
        a.set_xlabel("range pixel"); a.set_ylabel("azimuth pixel")
        fig.colorbar(im, ax=a, label="Ω (deg)")
    ax[2].plot(est_before.omega_range_deg, ":", lw=1, label="uncalibrated")
    ax[2].plot(est_after.omega_range_deg, "-", lw=1, label="calibrated")
    ax[2].axhline(0, color="k", lw=0.8)
    ax[2].set_ylim(-5, 5); ax[2].set_xlabel("range pixel"); ax[2].set_ylabel("Ω (deg)")
    ax[2].set_title("Ω per range line (spikes = corner-reflector columns)"); ax[2].legend()
    inj = [t["injected_deg"] for t in selftest]; rec = [t["recovered_deg"] for t in selftest]
    ax[3].plot([0, 21], [0, 21], "k--", lw=0.8, label="ideal")
    ax[3].plot(inj, rec, "o", color="k", label="recovered")
    ax[3].set_xlabel("injected Ω (deg)"); ax[3].set_ylabel("recovered Ω (deg)")
    ax[3].set_title("Self-test on input data"); ax[3].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Faraday rotation estimation and correction.")
    parser.add_argument("--input", type=Path, default=ROOT / "data",
                        help="folder with uncalibrated HH.npy, HV.npy, VH.npy, VV.npy (default: data/)")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output",
                        help="output folder (default: polcal/faraday/output/)")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW,
                        help=f"boxcar size for the Ω map (default: {DEFAULT_WINDOW})")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Loading uncalibrated channels from {args.input} ...")
    uncal = load(args.input)
    print(f"Scene shape: {uncal[0].shape}")

    # 1. self-test: inject known rotations into the input and recover them
    print("\nSelf-test: injecting known rotations into the input data")
    base = estimate_faraday(*uncal, window=args.window).omega_scene_deg
    selftest = []
    for injected in (1.0, 2.0, 5.0, 10.0, 20.0):
        rec = estimate_faraday(*apply_faraday(*uncal, np.radians(injected)),
                               window=args.window).omega_scene_deg - base
        selftest.append({"injected_deg": injected, "recovered_deg": round(rec, 4)})
        print(f"  injected {injected:5.1f} deg -> recovered {rec:7.3f} deg")

    # 2. estimate on the input
    est_before = estimate_faraday(*uncal, window=args.window)
    before = est_before.summary() | {"hv_vh_mismatch_db": hv_vh_mismatch_db(uncal)}

    # 3. correct and re-estimate
    omega = np.radians(before["omega_scene_deg"])
    cal = tuple(a.astype(np.complex64) for a in correct_faraday(*uncal, omega))
    est_after = estimate_faraday(*cal, window=args.window)
    after = est_after.summary() | {"hv_vh_mismatch_db": hv_vh_mismatch_db(cal)}
    change = channel_change(uncal, cal)

    # 4. save
    for c, arr in zip(CHANNELS, cal):
        np.save(args.output / f"calibrated_{c}.npy", arr)
    results = {"input": str(args.input), "selftest": selftest,
               "correction_applied_deg": float(np.degrees(omega)),
               "uncalibrated": before, "calibrated": after, "channel_change": change}
    (args.output / "faraday_results.json").write_text(json.dumps(results, indent=2))
    make_figure(est_before, est_after, selftest, args.output / "faraday_rotation.png")

    print_report(before, after, change, selftest, args.window)
    print(f"\nSaved to {args.output}")
    print("  calibrated_{HH,HV,VH,VV}.npy  (Faraday-corrected complex channels)")
    print("  faraday_results.json, faraday_rotation.png")


if __name__ == "__main__":
    main()
