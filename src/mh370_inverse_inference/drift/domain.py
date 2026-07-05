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


@dataclass(frozen=True, slots=True)
class EnvironmentalSample:
    current_speed_mps: float
    wind_speed_mps: float
    wave_height_m: float
    sea_surface_temperature_c: float

    def __post_init__(self) -> None:
        values = (
            self.current_speed_mps,
            self.wind_speed_mps,
            self.wave_height_m,
            self.sea_surface_temperature_c,
        )
        if not all(isfinite(value) for value in values):
            raise ValueError("environment values must be finite")
        if self.current_speed_mps < 0.0:
            raise ValueError("current speed must be non-negative")
        if self.wind_speed_mps < 0.0:
            raise ValueError("wind speed must be non-negative")
        if self.wave_height_m < 0.0:
            raise ValueError("wave height must be non-negative")


@dataclass(frozen=True, slots=True)
class DriftDomain:
    parameters: tuple[NumericRange, ...]

    def __post_init__(self) -> None:
        if not self.parameters:
            raise ValueError("at least one parameter is required")
        names = tuple(parameter.name for parameter in self.parameters)
        if len(set(names)) != len(names):
            raise ValueError("parameter names must be unique")

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(parameter.name for parameter in self.parameters)

    def validate_point(self, point: dict[str, float]) -> None:
        if set(point) != set(self.names):
            raise ValueError("point keys must match parameter names")
        for parameter in self.parameters:
            if not parameter.contains(point[parameter.name]):
                raise ValueError(f"{parameter.name} is outside its range")
