from __future__ import annotations

from pathlib import Path

import numpy as np

from polcal.ainsworth.calibration.models import PolSARImage


class PolSARIO:
    """I/O boundary for complex UAVSAR channel arrays."""

    CHANNELS = ("HH", "HV", "VH", "VV")

    @classmethod
    def load_npy(cls, directory: str | Path, mmap: bool = True) -> PolSARImage:
        directory = Path(directory)
        mode = "r" if mmap else None
        arrays = [
            np.load(directory / f"{channel}.npy", mmap_mode=mode)
            for channel in cls.CHANNELS
        ]
        return PolSARImage(*arrays)

    @classmethod
    def save_npy(cls, image: PolSARImage, directory: str | Path, prefix: str = "calibrated_") -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for channel, array in zip(cls.CHANNELS, (image.hh, image.hv, image.vh, image.vv)):
            np.save(directory / f"{prefix}{channel}.npy", array)
