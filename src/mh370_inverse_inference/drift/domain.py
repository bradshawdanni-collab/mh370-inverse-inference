"""Validation-only records for environmental data."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class NumericRange:
    name: str
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")
        if not isfinite(self.lower) or not isfinite(self.upper):
            raise ValueError("bounds must be finite")
        if self.upper < self.lower:
            raise ValueError("upper must not be below lower")

    def contains(self, value: float) -> bool:
        return isfinite(value) and self.lower <= value <= self.upper
