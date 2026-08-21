# Quegan Phase and Cross-Talk Calibration

Implementation of S. Quegan, "A Unified Algorithm for Phase and Cross-Talk
Calibration of Polarimetric Data — Theory and Observations," IEEE Trans.
Geosci. Remote Sensing, vol. 32, no. 1, 1994. Structured the same way as
`polcal/ainsworth`, and reuses its generic building blocks (`PolSARImage`,
scattering-vector/covariance construction, smoothing/interpolation, I/O, and
preview rendering) rather than duplicating them.

## Structure

```text
quegan/
├── main.py
├── README.md
└── calibration/
    ├── __init__.py
    ├── config.py          # immutable configuration
    ├── models.py           # domain/data objects (reuses PolSARImage from ainsworth)
    ├── core.py             # Quegan equations (22)-(30) and calibration transform (41)-(42)
    ├── estimator.py        # range-line estimation and HH-HV mask
    ├── smoothing.py         # re-exports ainsworth's interpolation + smoothing
    ├── pipeline.py          # complete image calibration orchestration
    ├── validation.py        # physical/numerical validation checks
    ├── visualization.py     # re-exports ainsworth's preview rendering
    ├── io.py                 # re-exports ainsworth's NumPy/UAVSAR channel I/O
    └── reporting.py          # run summaries
```

## Input / Output

Same convention as `polcal/ainsworth`: `HH.npy`, `HV.npy`, `VH.npy`, `VV.npy`
are read from the repository-root `data/` directory, and results are written
to `quegan/output/` — calibrated channel arrays (`calibrated_HH.npy`, etc.),
`uncalibrated_preview*.png` / `calibrated*.png` previews, and
`quegan_parameters.npz` diagnostics.

## Run

```bash
python -m polcal.quegan.main
```

The package API can also be used directly:

```python
from polcal.quegan.calibration import QueganCalibrator, QueganConfig, PolSARIO

config = QueganConfig()
image = PolSARIO.load_npy("data")
calibrated, diagnostics = QueganCalibrator(config).calibrate(image)
```

## Algorithm notes

- **Cross-talk ratios** `u, v, w, z` are solved directly and noniteratively
  from the observed covariance matrix via eqs. (22)-(25) — unlike Ainsworth's
  method, Quegan's algorithm requires no iteration.
- **Phase/gain parameter `alpha` and cross-polarized power term `beta`** have
  two algebraically independent solutions, eqs. (26)+(28) and (29)+(30). The
  `QueganConfig.solution` field (default `1`) selects which drives
  calibration; both are retained in diagnostics (`alpha1`, `alpha2`) since
  their disagreement is itself an indicator of the calibration's reliability
  for that range line, as discussed in the paper.
- **Calibration transform**: the paper's noiseless system matrix (eq. 41,
  with the unresolvable absolute gain `Y` and channel-imbalance ratio `k` set
  to 1, since relative calibration does not depend on them per Section IV) is
  inverted via least squares, `W = (A^H A)^-1 A^H` (eq. 42), and applied
  directly to each pixel's observation vector `(HH, VH, HV, VV)`.
- **Reciprocity** (`S12 = S21`, Section II.A assumption 2) means the method
  recovers a single cross-polarized scattering component `S21`; the
  calibrated `HV` and `VH` channels are therefore identical.
- Singular/invalid range lines are retained as missing estimates and
  interpolated before smoothing, matching the Ainsworth workflow.
