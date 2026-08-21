from __future__ import annotations
from pathlib import Path
from polcal.ainsworth.calibration import (
    AinsworthCalibrator,
    AinsworthConfig,
    CalibrationReporter,
    CalibrationValidator,
    DiagnosticStore,
    PolSARIO,
    SARVisualizer,
)
from polcal.utilities.plot_diagnostics import generate_diagnostic_plots


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data"
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading UAVSAR complex channels...")
    image = PolSARIO.load_npy(data_dir, mmap=True)
    print(f"Input shape: {image.shape}")

    visualizer = SARVisualizer()
    visualizer.linear_basis_rgb(image, output_dir / "uncalibrated_preview.png")
    visualizer.grayscale(image, output_dir / "uncalibrated_preview_gray.png")

    config = AinsworthConfig(
        stripe_half_width=10,
        correlation_threshold=0.2,
        smoothing_window=100,
        max_iterations=12,
        tolerance=1e-8,
    )

    print("\nRunning UAVSAR Ainsworth calibration...")
    calibrator = AinsworthCalibrator(config)
    calibrated, diagnostics = calibrator.calibrate(image, show_progress=True)

    print("\nSaving calibrated complex channels...")
    PolSARIO.save_npy(calibrated, output_dir)
    DiagnosticStore.save(diagnostics, output_dir / "ainsworth_parameters.npz")

    print("\nSaving calibrated preview...")
    visualizer.linear_basis_rgb(calibrated, output_dir / "calibrated.png")
    visualizer.grayscale(calibrated, output_dir / "calibrated_gray.png")

    CalibrationReporter.print_summary(diagnostics)

    # Optional spot-check of the middle range line.
    middle = image.rows // 2
    validator = CalibrationValidator(config)
    from polcal.ainsworth.calibration.estimator import RangeLineEstimator

    try:
        line_result = RangeLineEstimator(config).estimate(image, middle)
        idem = validator.idempotency_check(line_result.ainsworth.calibrated_covariance)
        print("\n--- Idempotency (\"do no harm\") check ---")
        for key, value in idem.items():
            print(f"{key}: {value}")
    except (ValueError, RuntimeError):
        print("\nIdempotency check skipped: middle range line could not be estimated.")

    print("\nGenerating diagnostic plots...")
    generate_diagnostic_plots(
        data_dir=data_dir,
        output_dir=output_dir,
        diagnostics_filename="ainsworth_parameters.npz",
    )


if __name__ == "__main__":
    main()
