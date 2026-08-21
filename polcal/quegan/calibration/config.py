from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueganConfig:
    """Configuration for the Quegan (1994) unified phase/cross-talk calibration."""

    epsilon: float = 1e-12
    stripe_half_width: int = 10
    correlation_window: int = 5
    correlation_threshold: float = 0.2
    smoothing_window: int = 100
    minimum_valid_pixels: int = 8
    positive_definite_tolerance: float = 1e-8
    idempotency_atol: float = 1e-6
    # Quegan's cross-talk removal equations (26)-(30) admit two algebraically
    # equivalent (alpha, beta) solutions; select which one drives calibration.
    solution: int = 1

    def __post_init__(self) -> None:
        if self.stripe_half_width < 0:
            raise ValueError("stripe_half_width must be >= 0")
        if self.correlation_window <= 0:
            raise ValueError("correlation_window must be > 0")
        if not 0 < self.correlation_threshold <= 1:
            raise ValueError("correlation_threshold must be in (0, 1]")
        if self.smoothing_window <= 0:
            raise ValueError("smoothing_window must be > 0")
        if self.minimum_valid_pixels <= 0:
            raise ValueError("minimum_valid_pixels must be > 0")
        if self.solution not in (1, 2):
            raise ValueError("solution must be 1 or 2")
