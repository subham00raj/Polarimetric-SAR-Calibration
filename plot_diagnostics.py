"""CLI wrapper for the Ainsworth calibration diagnostic plots.

Thin entry point over polcal.utilities.plot_diagnostics.generate_diagnostic_plots.
Both polcal/ainsworth/main.py and polcal/quegan/main.py call that function
directly after saving their diagnostics; run this script standalone to
regenerate the Ainsworth plots from already-saved output.
"""
from pathlib import Path

from polcal.utilities.plot_diagnostics import generate_diagnostic_plots

repo_root = Path(__file__).resolve().parent

if __name__ == "__main__":
    generate_diagnostic_plots(
        data_dir=repo_root / "data",
        output_dir=repo_root / "polcal" / "ainsworth" / "output",
        diagnostics_filename="ainsworth_parameters.npz",
    )
