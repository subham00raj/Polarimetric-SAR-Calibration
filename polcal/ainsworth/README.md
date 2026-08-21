# UAVSAR Ainsworth Cross-Talk Calibration

This refactor keeps the numerical processing from the original script but separates responsibilities into testable components.

## Structure

```text
ainsworth_calibration/
├── main.py
├── README.md
└── ainsworth_calibration/
    ├── __init__.py
    ├── config.py          # immutable configuration
    ├── models.py          # domain/data objects
    ├── core.py            # Ainsworth equations and matrix operations
    ├── estimator.py       # range-line estimation and HH-HV mask
    ├── smoothing.py       # interpolation + moving-average profiles
    ├── pipeline.py        # complete image calibration orchestration
    ├── validation.py      # physical/numerical validation checks
    ├── visualization.py   # preview rendering only
    ├── io.py              # NumPy/UAVSAR channel I/O
    └── reporting.py       # run summaries
```

## Input

Put `HH.npy`, `HV.npy`, `VH.npy`, and `VV.npy` in `data/` next to `main.py`.
The arrays must contain complex SAR data and have identical 2-D shapes.

## Run

```bash
cd ainsworth_calibration
python main.py
```

The package API can also be used directly:

```python
from ainsworth_calibration import (
    AinsworthCalibrator,
    AinsworthConfig,
    PolSARIO,
)

config = AinsworthConfig()
image = PolSARIO.load_npy("data")
calibrated, diagnostics = AinsworthCalibrator(config).calibrate(image)
```

## Important design choices

- User-facing channel order remains `HH, HV, VH, VV`.
- Internal UAVSAR paper order remains `HH, VH, HV, VV`.
- Visualization is isolated from calibration and never changes the complex data.
- Configuration is immutable and validated at construction time.
- Intermediate results are represented by dataclasses rather than untyped dictionaries.
- Singular/invalid range lines are retained as missing estimates and interpolated before smoothing, matching the original workflow.
- The original Ainsworth iteration equations and update ordering are preserved.
