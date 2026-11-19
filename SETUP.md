# Setup and Run Guide

This guide takes you from a fresh machine to a full run of the PolSAR
calibration pipeline: radiometric calibration with corner reflectors,
Ainsworth and Quegan cross-talk / channel-imbalance calibration, and the
Faraday rotation check, all on UAVSAR L-band data over Rosamond dry lake,
California.

Work through the sections in order. Every command is run from the
**repository root** unless the step says otherwise.

---

## 1. Requirements

| Item | Needed | Notes |
|---|---|---|
| OS | Linux, macOS, or Windows via WSL2 | Tested on Ubuntu (Linux 7.0) |
| Python | **3.14** | `uv` installs it for you |
| [uv](https://docs.astral.sh/uv/) | 0.11 or newer | Python and dependency manager |
| GDAL (system library) | 3.x | Needed by the `gdal` Python package |
| Disk | ~2 GB for the 3000 × 3000 subset | ~21 GB if you also download the full-resolution SLCs |
| RAM | 8 GB minimum, 16 GB recommended | The subset is 72 MB per channel; the full scene is ~4.8 GB per channel |
| GPU | Optional | Only `polcal/covariance` uses PyTorch |

---

## 2. Install

### 2.1 Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# restart the shell, then check
uv --version
```

### 2.2 Install the GDAL system library

The `gdal` Python package compiles against your system GDAL, so install that
first.

```bash
# Ubuntu / Debian / WSL
sudo apt update
sudo apt install -y gdal-bin libgdal-dev build-essential

# macOS (Homebrew)
brew install gdal
```

Check the version:

```bash
gdal-config --version
```

### 2.3 Get the code

```bash
git clone https://github.com/subham00raj/Polarimetric-SAR-Calibration.git
cd Polarimetric-SAR-Calibration
```

### 2.4 Install the Python dependencies

```bash
uv python install 3.14
uv sync
```

`uv sync` creates `.venv/` and installs everything from `pyproject.toml` and
`uv.lock`.

**If the `gdal` package fails to build**, the Python package version must
match the system library. Pin it to your system version and sync again:

```bash
uv add "gdal==$(gdal-config --version)"
uv sync
```

### 2.5 Install the two packages missing from `pyproject.toml`

Two modules import packages that are not yet listed as dependencies:

| Package | Used by | Install |
|---|---|---|
| `tifffile` | `polcal/radiocal/radiometric_calibration.py` | `uv add tifffile` |
| `torch` | `polcal/covariance/covariance.py` (and optional GPU paths) | `uv add torch` (CPU build is fine) |

The Ainsworth, Quegan and Faraday pipelines do **not** need either package.

### 2.6 Check the install

```bash
uv run python -c "from osgeo import gdal; import numpy, scipy, matplotlib; print('GDAL', gdal.__version__, '- OK')"
```

---

## 3. Get the data

All data goes in `data/` (git ignores this folder, so it is not in the
repository).

```text
data/
├── 2020-09-16_0000_Rosamond-corner-reflectors_with_plate_motion.csv   # surveyed corner reflectors
├── Input.csv                                # reflectors located in the subset (step 5.1)
├── HH.npy  HV.npy  VH.npy  VV.npy           # 3000 x 3000 complex64 subset  <- used by all pipelines
├── HH.tif  HV.tif  VH.tif  VV.tif           # same subset as GeoTIFF       <- used by radiocal / find_cr
├── Rosamd_35012_04_BC_s1_2x8.llh            # lat / lon / height
└── Rosamd_35012_04_BC_s1_2x8.lkv            # look vectors
```

**Shortcut:** if someone hands you a copy of `data/` with these files, put it
in the repository root and skip to [Section 4](#4-configure-env).

### 3.1 Download from JPL

Dataset: UAVSAR flight line `Rosamd_35012`, flight `16074`, data take `005`,
acquired **16 Sep 2020**, L-band quad-pol, Release 26.

```bash
mkdir -p data
cd data
uv run python ../polcal/utilities/get_uavsar_data.py
cd ..
```

The script downloads into the current folder, which is why it runs from inside
`data/`. It fetches:

* the corner-reflector CSV for 16-09-2020,
* four full-resolution SLCs (`..._L090HH_04_BC_s1_1x1.slc`, and the same for
  HV, VH, VV), each **61349 × 9874** complex64 (~4.8 GB),
* the matching `.ann` annotation files,
* the `.llh` and `.lkv` files.

The download is about 21 GB. The JPL server can be slow, so expect it to take
a while.

### 3.2 Cut the 3000 × 3000 study subset

The pipelines run on a subset that contains the corner-reflector array. Its
position is defined in `config.py` (`x_start = 2000`, `y_start = 41000`,
`x_size = y_size = 3000`). Run this from the repository root:

```bash
uv run python - <<'EOF'
import numpy as np
from osgeo import gdal
import config

rows, cols = config.row_1x1, config.col_1x1
y0, x0 = config.y_start, config.x_start
ny, nx = config.y_size, config.x_size

for pol in ("HH", "HV", "VH", "VV"):
    slc = np.memmap(f"data/Rosamd_35012_16074_005_160920_L090{pol}_04_BC_s1_1x1.slc",
                    dtype=np.complex64, mode="r", shape=(rows, cols))
    sub = np.array(slc[y0:y0 + ny, x0:x0 + nx])
    np.save(f"data/{pol}.npy", sub)
    ds = gdal.GetDriverByName("GTiff").Create(f"data/{pol}.tif", nx, ny, 1, gdal.GDT_CFloat32)
    ds.GetRasterBand(1).WriteArray(sub)
    ds.FlushCache(); ds = None
    print(pol, sub.shape, sub.dtype)
EOF
```

You can delete the large `.slc` files afterwards, unless you want to run on
the full scene.

**Sanity check:** in `|HH|` the corner reflectors should show up as a diagonal
line of bright points in the lower-left half of the subset:

```bash
uv run python -c "import numpy as np, matplotlib.pyplot as plt; a=np.abs(np.load('data/HH.npy')); plt.imsave('hh_check.png', a, cmap='gray', vmin=0, vmax=0.2); print('wrote hh_check.png')"
```

---

## 4. Configure `.env`

The radiometric-calibration, covariance and corner-reflector scripts read
their file paths from a `.env` file in the repository root. Git ignores
`.env`, so create it yourself:

```bash
cat > .env <<EOF
HH_path=$PWD/data/Rosamd_35012_16074_005_160920_L090HH_04_BC_s1_1x1.slc
HV_path=$PWD/data/Rosamd_35012_16074_005_160920_L090HV_04_BC_s1_1x1.slc
VH_path=$PWD/data/Rosamd_35012_16074_005_160920_L090VH_04_BC_s1_1x1.slc
VV_path=$PWD/data/Rosamd_35012_16074_005_160920_L090VV_04_BC_s1_1x1.slc
lkv_path=$PWD/data/Rosamd_35012_04_BC_s1_2x8.lkv
llh_path=$PWD/data/Rosamd_35012_04_BC_s1_2x8.llh
csv_path=$PWD/data/2020-09-16_0000_Rosamond-corner-reflectors_with_plate_motion.csv
Input_csv_path=$PWD/data/Input.csv
HH_tif_path=$PWD/data/HH.tif
HV_tif_path=$PWD/data/HV.tif
VH_tif_path=$PWD/data/VH.tif
VV_tif_path=$PWD/data/VV.tif
output_folder_path=$PWD/output
covariance_file_path=$PWD/output/covariance
EOF
mkdir -p output/covariance
```

The Ainsworth, Quegan and Faraday pipelines do not use `.env`; they read
`data/*.npy` directly.

---

## 5. Run the pipeline

Run the steps in this order. Always launch them with `python -m` from the
repository root, so that `import polcal` works.

| Step | Command | Needs | Writes to | Time (subset) |
|---|---|---|---|---|
| 5.1 Locate corner reflectors | `uv run python -m polcal.utilities.find_cr` | `.env`, `.tif`, `.llh`, CR CSV | `data/Input.csv` | < 1 min |
| 5.2 Radiometric calibration | `uv run python -m polcal.radiocal.radiometric_calibration` | `.env`, `Input.csv`, `tifffile` | `output/*_calibrated.tiff`, `output/Output.csv` | ~1 min |
| 5.3 Ainsworth calibration | `uv run python -m polcal.ainsworth.main` | `data/*.npy` | `polcal/ainsworth/output/` | a few minutes |
| 5.4 Quegan calibration | `uv run python -m polcal.quegan.main` | `data/*.npy` | `polcal/quegan/output/` | a few minutes |
| 5.5 Faraday rotation check | `uv run python -m polcal.faraday.main` | step 5.3 output | `polcal/faraday/output/` | ~1 min |
| 5.6 Re-plot diagnostics (optional) | `uv run python plot_diagnostics.py` | step 5.3 output | `polcal/ainsworth/output/` | < 1 min |

Notes:

* **5.1** is optional if `data/Input.csv` already exists; it ships with the
  data. It opens a matplotlib window at the end. Close it to finish.
* **5.2** also opens a preview window at the end.
* **5.3 and 5.4** run the full pipeline: covariance per range line,
  parameter estimation, smoothing, applying the correction, previews, a summary
  printed to the console, and diagnostic plots. On the full 61349 × 9874 scene
  they take about **2.0 h** (Ainsworth) and **1.6 h** (Quegan).
* **5.5** self-tests the Bickel–Bates estimator by injecting known rotations,
  estimates Faraday rotation Ω on the uncalibrated and the Ainsworth-calibrated
  data, and applies the correction. Expected result: Ω ≈ 0° after calibration,
  because UAVSAR flies below the ionosphere.

Pauli and Yamaguchi decompositions are library functions in
`polcal/utilities/decomposition.py` (`pauli_rgb`, `yamaguchi_rgb`). Call them
on the uncalibrated and calibrated arrays from a notebook or script.

---

## 6. What you should get

| Folder | Key files |
|---|---|
| `polcal/ainsworth/output/` | `calibrated_{HH,HV,VH,VV}.npy`, `ainsworth_parameters.npz` (u, v, w, z, α per range line), `calibrated.png`, `calibrated_hv_vs_vh_scatter.png`, `calibrated_hv_vh_power_db.png` |
| `polcal/quegan/output/` | the same set of files for the Quegan model |
| `polcal/faraday/output/` | `faraday_results.json`, `faraday_rotation.png`, `faraday_corrected_*.npy` |
| `output/` | radiometrically calibrated / uncalibrated GeoTIFFs, `Output.csv` |

Reference numbers from the thesis, to check a run against:

* Cross-talk reduction: **12–27 dB** (Ainsworth), **5–31 dB** (Quegan)
* |α|: **−6.25 to +1.25 dB** (Ainsworth), **−5.35 to +18.55 dB** (Quegan)
* Faraday rotation on Ainsworth-calibrated data: **≈ +0.08°**

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'polcal'` | Run from the repository root with `python -m polcal....`, not `python polcal/.../main.py` |
| `gdal` fails to build during `uv sync` | Install `libgdal-dev` (section 2.2), then pin `gdal==$(gdal-config --version)` |
| `ModuleNotFoundError: tifffile` / `torch` | `uv add tifffile` / `uv add torch` (section 2.5) |
| `TypeError: expected str ... NoneType` in radiocal / find_cr / covariance | `.env` is missing or a key is misspelt (section 4) |
| `FileNotFoundError: data/HH.npy` | Cut the subset first (section 3.2) |
| `FileNotFoundError: .../ainsworth/output/calibrated_HH.npy` when running Faraday | Run step 5.3 first |
| `ValueError: cannot reshape` / memmap size error on `.slc` | The file is incomplete or the wrong resolution: the 1x1 SLC must be exactly 61349 × 9874 × 8 bytes |
| Out of memory | Run on the 3000 × 3000 subset; the full scene needs much more RAM |
| `requires-python >=3.14` error | `uv python install 3.14`, then `uv sync` |

---

## 8. Repository map

```text
config.py                    scene size, subset window, look angles
plot_diagnostics.py          re-plot Ainsworth diagnostics from saved output
polcal/
├── utilities/               data download, reading, CR finder, incidence angle,
│                            polarimetric signatures, decompositions, plotting
├── radiocal/                corner-reflector radiometric calibration
├── covariance/              windowed covariance matrices (PyTorch)
├── ainsworth/               Ainsworth et al. (2006) iterative calibration
│   └── calibration/         config, estimator, core, smoothing, validation, I/O
├── quegan/                  Quegan (1994) closed-form calibration (same layout)
└── faraday/                 Bickel–Bates Faraday rotation estimate and correction
```
