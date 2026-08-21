from __future__ import annotations

import numpy as np

from polcal.ainsworth.calibration.models import CalibrationDiagnostics


class CalibrationReporter:
    """Human-readable run summary."""

    @staticmethod
    def print_summary(diagnostics: CalibrationDiagnostics) -> None:
        gamma = diagnostics.gamma
        iterations = diagnostics.iterations
        converged = diagnostics.converged
        validation = diagnostics.validation_passed

        print("\n==========================================")
        print(" AINSWORTH CALIBRATION SUMMARY")
        print("==========================================")
        print(f"Range lines:              {len(gamma)}")
        print(f"Converged lines:           {np.sum(converged)}/{len(converged)}")
        print(f"Maximum iterations:       {iterations.max()}")

        active = iterations > 0
        mean_iterations = iterations[active].mean() if np.any(active) else float("nan")
        print(f"Mean iterations:           {mean_iterations:.2f}")
        print(f"Maximum gamma:             {np.nanmax(gamma):.3e}")

        for name, values in (("u", diagnostics.u), ("v", diagnostics.v),
                             ("w", diagnostics.w), ("z", diagnostics.z),
                             ("alpha", diagnostics.alpha)):
            print(
                f"|{name}| range:                 "
                f"{np.nanmin(np.abs(values)):.4e} to {np.nanmax(np.abs(values)):.4e}"
            )
        print(f"Lines passing validation: {np.sum(validation)}/{len(validation)}")
