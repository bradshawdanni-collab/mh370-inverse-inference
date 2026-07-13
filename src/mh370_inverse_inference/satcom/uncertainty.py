"""Deterministic slant-range uncertainty-band construction."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from mh370_inverse_inference.satcom.locus import (
    SurfaceLocusResult,
    generate_surface_locus,
)
from mh370_inverse_inference.satcom.satellite import SatellitePosition

BandIdentity = Literal["lower", "nominal", "upper"]
_BAND_ORDER: tuple[BandIdentity, ...] = ("lower", "nominal", "upper")


@dataclass(frozen=True, slots=True)
class SlantRangeUncertainty:
    """Declared range values with timing uncertainty kept separate from bias."""

    nominal_range_m: float
    timing_range_uncertainty_m: float
    satellite_position_bias_m: float = 0.0

    def __post_init__(self) -> None:
        _require_positive_finite(self.nominal_range_m, "nominal_range_m")
        _require_non_negative_finite(
            self.timing_range_uncertainty_m,
            "timing_range_uncertainty_m",
        )
        _require_non_negative_finite(
            self.satellite_position_bias_m,
            "satellite_position_bias_m",
        )
        if self.lower_range_m <= 0.0:
            raise ValueError("lower_range_m must be greater than zero")

    @property
    def lower_range_m(self) -> float:
        """Return the deterministic lower timing-derived range bound."""
        return float(self.nominal_range_m - self.timing_range_uncertainty_m)

    @property
    def upper_range_m(self) -> float:
        """Return the deterministic upper timing-derived range bound."""
        return float(self.nominal_range_m + self.timing_range_uncertainty_m)

    def ordered_ranges(self) -> tuple[tuple[BandIdentity, float], ...]:
        """Return lower, nominal, and upper ranges in canonical order."""
        ranges = {
            "lower": self.lower_range_m,
            "nominal": float(self.nominal_range_m),
            "upper": self.upper_range_m,
        }
        return tuple((identity, ranges[identity]) for identity in _BAND_ORDER)


@dataclass(frozen=True, slots=True)
class SlantRangeBand:
    """One named deterministic locus in an uncertainty-band result."""

    identity: BandIdentity
    target_range_m: float
    locus: SurfaceLocusResult

    def __post_init__(self) -> None:
        if self.identity not in _BAND_ORDER:
            raise ValueError("identity must be lower, nominal, or upper")
        _require_positive_finite(self.target_range_m, "target_range_m")
        if type(self.locus) is not SurfaceLocusResult:
            raise TypeError("locus must be SurfaceLocusResult")
        if self.locus.target_range_m != float(self.target_range_m):
            raise ValueError("locus target range must match target_range_m")


@dataclass(frozen=True, slots=True)
class SlantRangeUncertaintyBands:
    """Immutable lower, nominal, and upper surface-locus collection."""

    uncertainty: SlantRangeUncertainty
    bands: tuple[SlantRangeBand, ...]

    def __post_init__(self) -> None:
        if type(self.uncertainty) is not SlantRangeUncertainty:
            raise TypeError("uncertainty must be SlantRangeUncertainty")
        if type(self.bands) is not tuple:
            raise TypeError("bands must be tuple")
        if any(type(band) is not SlantRangeBand for band in self.bands):
            raise TypeError("bands must contain SlantRangeBand values")
        if tuple(band.identity for band in self.bands) != _BAND_ORDER:
            raise ValueError("bands must be ordered lower, nominal, upper")
        expected_ranges = tuple(
            target_range_m
            for _, target_range_m in self.uncertainty.ordered_ranges()
        )
        actual_ranges = tuple(band.target_range_m for band in self.bands)
        if actual_ranges != expected_ranges:
            raise ValueError("band target ranges must match uncertainty bounds")
        satellites = tuple(band.locus.satellite for band in self.bands)
        if satellites[1:] != satellites[:-1]:
            raise ValueError("all band loci must use the same satellite position")


def generate_uncertainty_bands(
    satellite: SatellitePosition,
    uncertainty: SlantRangeUncertainty,
    *,
    tolerance_m: float = 1.0,
    longitude_step_deg: float = 1.0,
    latitude_step_deg: float = 1.0,
    minimum_longitude_deg: float = -180.0,
    maximum_longitude_deg: float = 180.0,
    minimum_latitude_deg: float = -90.0,
    maximum_latitude_deg: float = 90.0,
    maximum_iterations: int = 64,
) -> SlantRangeUncertaintyBands:
    """Generate canonical lower, nominal, and upper L0.2 surface loci."""
    if type(satellite) is not SatellitePosition:
        raise TypeError("satellite must be SatellitePosition")
    if type(uncertainty) is not SlantRangeUncertainty:
        raise TypeError("uncertainty must be SlantRangeUncertainty")

    bands = tuple(
        SlantRangeBand(
            identity=identity,
            target_range_m=target_range_m,
            locus=generate_surface_locus(
                satellite,
                target_range_m,
                tolerance_m=tolerance_m,
                longitude_step_deg=longitude_step_deg,
                latitude_step_deg=latitude_step_deg,
                minimum_longitude_deg=minimum_longitude_deg,
                maximum_longitude_deg=maximum_longitude_deg,
                minimum_latitude_deg=minimum_latitude_deg,
                maximum_latitude_deg=maximum_latitude_deg,
                maximum_iterations=maximum_iterations,
            ),
        )
        for identity, target_range_m in uncertainty.ordered_ranges()
    )
    return SlantRangeUncertaintyBands(uncertainty=uncertainty, bands=bands)


def _require_positive_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero")


def _require_non_negative_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
