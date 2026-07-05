"""Deterministic bounded search-domain primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite, prod


@dataclass(frozen=True, slots=True)
class SearchDimension:
    """One inclusive scalar search dimension."""

    name: str
    lower: float
    upper: float
    step: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be non-empty")
        for field_name, value in (
            ("lower", self.lower),
            ("upper", self.upper),
            ("step", self.step),
        ):
            if not isfinite(value):
                raise ValueError(f"{field_name} must be finite")
        if self.upper < self.lower:
            raise ValueError("upper must be greater than or equal to lower")
        if self.step <= 0.0:
            raise ValueError("step must be positive")

    @property
    def count(self) -> int:
        """Return the number of deterministic grid values in this dimension."""
        return floor((self.upper - self.lower) / self.step) + 1

    def value_at(self, index: int) -> float:
        """Return the deterministic value at a zero-based index."""
        if index < 0 or index >= self.count:
            raise IndexError("dimension index out of range")
        return self.lower + self.step * index

    def normalize(self, value: float) -> float:
        """Map a value in bounds to the unit interval."""
        if not isfinite(value):
            raise ValueError("value must be finite")
        if value < self.lower or value > self.upper:
            raise ValueError("value must be within dimension bounds")
        if self.upper == self.lower:
            return 0.0
        return (value - self.lower) / (self.upper - self.lower)


@dataclass(frozen=True, slots=True)
class SearchDomain:
    """Ordered container for deterministic search dimensions."""

    dimensions: tuple[SearchDimension, ...]

    def __post_init__(self) -> None:
        if not self.dimensions:
            raise ValueError("at least one search dimension is required")
        names = tuple(dimension.name for dimension in self.dimensions)
        if len(set(names)) != len(names):
            raise ValueError("dimension names must be unique")

    @property
    def names(self) -> tuple[str, ...]:
        """Return dimension names in deterministic order."""
        return tuple(dimension.name for dimension in self.dimensions)

    @property
    def candidate_count(self) -> int:
        """Return total deterministic grid candidate count."""
        return prod(dimension.count for dimension in self.dimensions)

    def normalize_point(self, point: dict[str, float]) -> dict[str, float]:
        """Normalize one named point according to domain order and bounds."""
        if set(point) != set(self.names):
            raise ValueError("point keys must exactly match search dimensions")
        return {
            dimension.name: dimension.normalize(point[dimension.name])
            for dimension in self.dimensions
        }
