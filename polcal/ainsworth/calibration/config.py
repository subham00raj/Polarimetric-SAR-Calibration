from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AinsworthConfig:
    """Configuration for UAVSAR/Ainsworth cross-talk calibration."""

    epsilon: float = 1e-12
    stripe_half_width: int = 10
    correlation_window: int = 5
    correlation_threshold: float = 0.2
    smoothing_window: int = 100
    max_iterations: int = 12
    tolerance: float = 1e-8
    minimum_valid_pixels: int = 8
    positive_definite_tolerance: float = 1e-8
    idempotency_atol: float = 1e-6

    def __post_init__(self) -> None:
        if self.stripe_half_width < 0:
            raise ValueError("stripe_half_width must be >= 0")
        if self.correlation_window <= 0:
            raise ValueError("correlation_window must be > 0")
        if not 0 < self.correlation_threshold <= 1:
            raise ValueError("correlation_threshold must be in (0, 1]")
        if self.smoothing_window <= 0:
            raise ValueError("smoothing_window must be > 0")
        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be > 0")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be > 0")
        if self.minimum_valid_pixels <= 0:
            raise ValueError("minimum_valid_pixels must be > 0")
