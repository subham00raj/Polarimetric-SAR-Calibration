from __future__ import annotations

import numpy as np

from polcal.quegan.calibration.models import CalibrationDiagnostics


class CalibrationReporter:
    """Human-readable run summary."""

    @staticmethod
    def print_summary(diagnostics: CalibrationDiagnostics) -> None:
        valid_pixels = diagnostics.valid_pixels
        validation = diagnostics.validation_passed

        print("\n==========================================")
        print(" QUEGAN CALIBRATION SUMMARY")
        print("==========================================")
        print(f"Range lines:              {len(valid_pixels)}")
        print(f"Mean valid pixels/line:   {valid_pixels.mean():.1f}")

        for name, values in (("u", diagnostics.u), ("v", diagnostics.v),
                             ("w", diagnostics.w), ("z", diagnostics.z),
                             ("alpha", diagnostics.alpha), ("beta", diagnostics.beta)):
            print(
                f"|{name}| range:                 "
                f"{np.nanmin(np.abs(values)):.4e} to {np.nanmax(np.abs(values)):.4e}"
            )

        disagreement = np.abs(diagnostics.alpha1 - diagnostics.alpha2)
        print(f"Mean |alpha1 - alpha2|:    {np.nanmean(disagreement):.4e}")
        print(f"Lines passing validation: {np.sum(validation)}/{len(validation)}")
