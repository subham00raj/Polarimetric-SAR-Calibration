from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from polcal.faraday import apply_faraday, correct_faraday, estimate_faraday

CHANNELS = ("HH", "HV", "VH", "VV")


def load(directory: Path, prefix: str = "") -> tuple[np.ndarray, ...]:
    return tuple(np.load(directory / f"{prefix}{c}.npy").astype(np.complex64) for c in CHANNELS)


def change_metrics(before, after) -> dict:
    out = {}
    for name, b, a in zip(CHANNELS, before, after):
        pb = np.abs(b) ** 2
        pa = np.abs(a) ** 2
        out[name] = {
            "mean_power_change_pct": float(100 * (pa.mean() - pb.mean()) / pb.mean()),
            "median_abs_amplitude_change_pct": float(
                100 * np.median(np.abs(np.abs(a) - np.abs(b)) / (np.abs(b) + 1e-12))
            ),
        }
    hv_vh = lambda s: float(10 * np.log10(np.mean(np.abs(s[1]) ** 2) / np.mean(np.abs(s[2]) ** 2)))
    out["HV_VH_power_ratio_db"] = {"before": hv_vh(before), "after": hv_vh(after)}
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading uncalibrated and Ainsworth-calibrated channels...")
    uncal = load(root / "data")
    cal = load(root / "polcal" / "ainsworth" / "output", prefix="calibrated_")
    print(f"Scene shape: {uncal[0].shape}")

    # 1. self-test on real data
    print("\nSelf-test: injecting known rotations into the calibrated data")
    base = estimate_faraday(*cal).omega_scene_deg
    selftest = []
    for injected in (1.0, 2.0, 5.0, 10.0, 20.0):
        rotated = apply_faraday(*cal, np.radians(injected))
        rec = estimate_faraday(*rotated).omega_scene_deg - base
        selftest.append({"injected_deg": injected, "recovered_deg": round(rec, 4)})
        print(f"  injected {injected:5.1f} deg -> recovered {rec:7.3f} deg")

    # 2. estimates
    results = {"selftest": selftest}
    estimates = {}
    for label, img in (("uncalibrated", uncal), ("ainsworth_calibrated", cal)):
        est = estimate_faraday(*img, window=15)
        estimates[label] = est
        results[label] = est.summary()
        s = results[label]
        print(f"\n{label}: scene Omega = {s['omega_scene_deg']:+.3f} deg | "
              f"map median {s['omega_map_median_deg']:+.3f}, std {s['omega_map_std_deg']:.3f} deg | "
              f"range-profile std {s['omega_range_std_deg']:.3f} deg")

    # 3. apply correction to the calibrated data
    omega = np.radians(results["ainsworth_calibrated"]["omega_scene_deg"])
    corrected = correct_faraday(*cal, omega)
    results["correction_applied_deg"] = float(np.degrees(omega))
    results["correction_effect"] = change_metrics(cal, corrected)
    print(f"\nApplied correction with Omega = {np.degrees(omega):+.3f} deg")
    for c in CHANNELS:
        m = results["correction_effect"][c]
        print(f"  {c}: mean power change {m['mean_power_change_pct']:+.4f}% | "
              f"median |amplitude| change {m['median_abs_amplitude_change_pct']:.4f}%")
    r = results["correction_effect"]["HV_VH_power_ratio_db"]
    print(f"  HV/VH power ratio: {r['before']:+.4f} dB -> {r['after']:+.4f} dB")

    for c, arr in zip(CHANNELS, corrected):
        np.save(out_dir / f"faraday_corrected_{c}.npy", arr.astype(np.complex64))
    (out_dir / "faraday_results.json").write_text(json.dumps(results, indent=2))

    # figure
    fig, ax = plt.subplots(1, 3, figsize=(17, 4.8))
    est = estimates["ainsworth_calibrated"]
    im = ax[0].imshow(est.omega_map_deg, cmap="RdBu_r", vmin=-5, vmax=5)
    ax[0].set_title(f"Ω map, Ainsworth-calibrated ({est.window}×{est.window} boxcar)")
    ax[0].set_xlabel("range pixel"); ax[0].set_ylabel("azimuth pixel")
    fig.colorbar(im, ax=ax[0], label="Ω (deg)")
    for label, ls in (("uncalibrated", ":"), ("ainsworth_calibrated", "-")):
        ax[1].plot(estimates[label].omega_range_deg, ls, lw=1, label=label.replace("_", " "))
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set_ylim(-5, 5); ax[1].set_xlabel("range pixel"); ax[1].set_ylabel("Ω (deg)")
    ax[1].set_title("Ω per range line"); ax[1].legend()
    inj = [t["injected_deg"] for t in selftest]; recv = [t["recovered_deg"] for t in selftest]
    ax[2].plot([0, 21], [0, 21], "k--", lw=0.8, label="ideal")
    ax[2].plot(inj, recv, "o", color="k", label="recovered")
    ax[2].set_xlabel("injected Ω (deg)"); ax[2].set_ylabel("recovered Ω (deg)")
    ax[2].set_title("Self-test on real data"); ax[2].legend()
    fig.tight_layout()
    fig.savefig(out_dir / "faraday_rotation.png", dpi=200)
    print(f"\nSaved results to {out_dir}")


if __name__ == "__main__":
    main()
