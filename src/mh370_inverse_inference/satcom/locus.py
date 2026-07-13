"""Deterministic Earth-surface slant-range locus generation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.slant_range import slant_range_m
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    geodetic_to_ecef,
)


@dataclass(frozen=True, slots=True)
class SurfaceLocusPoint:
    """One validated point on the zero-altitude WGS84 surface."""

    geodetic: GeodeticPoint
    ecef: ECEFPoint

    def __post_init__(self) -> None:
        if type(self.geodetic) is not GeodeticPoint:
            raise TypeError("geodetic must be GeodeticPoint")
        if self.geodetic.altitude_m != 0.0:
            raise ValueError("surface locus points must have zero altitude")
        if type(self.ecef) is not ECEFPoint:
            raise TypeError("ecef must be ECEFPoint")
        if self.ecef != geodetic_to_ecef(self.geodetic):
            raise ValueError("ecef must match geodetic coordinates")


@dataclass(frozen=True, slots=True)
class SurfaceLocusResult:
    """Immutable deterministic locus result and declared solver metadata."""

    satellite: SatellitePosition
    target_range_m: float
    tolerance_m: float
    longitude_step_deg: float
    latitude_step_deg: float
    points: tuple[SurfaceLocusPoint, ...]

    def __post_init__(self) -> None:
        if type(self.satellite) is not SatellitePosition:
            raise TypeError("satellite must be SatellitePosition")
        _require_positive_finite(self.target_range_m, "target_range_m")
        _require_positive_finite(self.tolerance_m, "tolerance_m")
        _require_positive_finite(self.longitude_step_deg, "longitude_step_deg")
        _require_positive_finite(self.latitude_step_deg, "latitude_step_deg")
        if type(self.points) is not tuple:
            raise TypeError("points must be tuple")
        if any(type(point) is not SurfaceLocusPoint for point in self.points):
            raise TypeError("points must contain SurfaceLocusPoint values")


def _require_positive_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero")


def _validate_bounds(
    minimum_longitude_deg: float,
    maximum_longitude_deg: float,
    minimum_latitude_deg: float,
    maximum_latitude_deg: float,
) -> None:
    for value, name in (
        (minimum_longitude_deg, "minimum_longitude_deg"),
        (maximum_longitude_deg, "maximum_longitude_deg"),
        (minimum_latitude_deg, "minimum_latitude_deg"),
        (maximum_latitude_deg, "maximum_latitude_deg"),
    ):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be a real number")
        if not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")
    if not -180.0 <= minimum_longitude_deg < maximum_longitude_deg <= 180.0:
        raise ValueError("longitude bounds must satisfy -180 <= minimum < maximum <= 180")
    if not -90.0 <= minimum_latitude_deg < maximum_latitude_deg <= 90.0:
        raise ValueError("latitude bounds must satisfy -90 <= minimum < maximum <= 90")


def _axis_values(minimum: float, maximum: float, step: float) -> tuple[float, ...]:
    count = int(math.floor((maximum - minimum) / step))
    values = [minimum + index * step for index in range(count + 1)]
    if values[-1] < maximum:
        values.append(maximum)
    else:
        values[-1] = maximum
    return tuple(values)


def _residual_m(
    latitude_deg: float,
    longitude_deg: float,
    satellite: SatellitePosition,
    target_range_m: float,
) -> float:
    geodetic = GeodeticPoint(latitude_deg, longitude_deg, 0.0)
    return slant_range_m(geodetic_to_ecef(geodetic), satellite) - target_range_m


def _refine_root(
    lower_latitude_deg: float,
    upper_latitude_deg: float,
    longitude_deg: float,
    satellite: SatellitePosition,
    target_range_m: float,
    tolerance_m: float,
    maximum_iterations: int,
) -> float:
    lower = lower_latitude_deg
    upper = upper_latitude_deg
    lower_residual = _residual_m(lower, longitude_deg, satellite, target_range_m)
    for _ in range(maximum_iterations):
        midpoint = (lower + upper) / 2.0
        midpoint_residual = _residual_m(
            midpoint,
            longitude_deg,
            satellite,
            target_range_m,
        )
        if abs(midpoint_residual) <= tolerance_m:
            return midpoint
        if math.copysign(1.0, midpoint_residual) == math.copysign(
            1.0,
            lower_residual,
        ):
            lower = midpoint
            lower_residual = midpoint_residual
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def generate_surface_locus(
    satellite: SatellitePosition,
    target_range_m: float,
    *,
    tolerance_m: float = 1.0,
    longitude_step_deg: float = 1.0,
    latitude_step_deg: float = 1.0,
    minimum_longitude_deg: float = -180.0,
    maximum_longitude_deg: float = 180.0,
    minimum_latitude_deg: float = -90.0,
    maximum_latitude_deg: float = 90.0,
    maximum_iterations: int = 64,
) -> SurfaceLocusResult:
    """Generate a deterministic ordered WGS84 surface slant-range locus."""
    if type(satellite) is not SatellitePosition:
        raise TypeError("satellite must be SatellitePosition")
    _require_positive_finite(target_range_m, "target_range_m")
    _require_positive_finite(tolerance_m, "tolerance_m")
    _require_positive_finite(longitude_step_deg, "longitude_step_deg")
    _require_positive_finite(latitude_step_deg, "latitude_step_deg")
    _validate_bounds(
        minimum_longitude_deg,
        maximum_longitude_deg,
        minimum_latitude_deg,
        maximum_latitude_deg,
    )
    if type(maximum_iterations) is not int:
        raise TypeError("maximum_iterations must be int")
    if maximum_iterations <= 0:
        raise ValueError("maximum_iterations must be greater than zero")

    longitudes = _axis_values(
        minimum_longitude_deg,
        maximum_longitude_deg,
        longitude_step_deg,
    )
    latitudes = _axis_values(
        minimum_latitude_deg,
        maximum_latitude_deg,
        latitude_step_deg,
    )
    points: list[SurfaceLocusPoint] = []
    seen: set[tuple[float, float]] = set()

    for longitude_deg in longitudes:
        previous_latitude = latitudes[0]
        previous_residual = _residual_m(
            previous_latitude,
            longitude_deg,
            satellite,
            target_range_m,
        )
        candidates: list[float] = []
        if abs(previous_residual) <= tolerance_m:
            candidates.append(previous_latitude)

        for latitude_deg in latitudes[1:]:
            residual = _residual_m(
                latitude_deg,
                longitude_deg,
                satellite,
                target_range_m,
            )
            if abs(residual) <= tolerance_m:
                candidates.append(latitude_deg)
            elif previous_residual * residual < 0.0:
                candidates.append(
                    _refine_root(
                        previous_latitude,
                        latitude_deg,
                        longitude_deg,
                        satellite,
                        target_range_m,
                        tolerance_m,
                        maximum_iterations,
                    )
                )
            previous_latitude = latitude_deg
            previous_residual = residual

        for latitude_deg in candidates:
            key = (round(longitude_deg, 12), round(latitude_deg, 12))
            if key in seen:
                continue
            geodetic = GeodeticPoint(latitude_deg, longitude_deg, 0.0)
            ecef = geodetic_to_ecef(geodetic)
            if abs(slant_range_m(ecef, satellite) - target_range_m) > tolerance_m:
                continue
            seen.add(key)
            points.append(SurfaceLocusPoint(geodetic=geodetic, ecef=ecef))

    points.sort(key=lambda point: (point.geodetic.longitude_deg, point.geodetic.latitude_deg))
    return SurfaceLocusResult(
        satellite=satellite,
        target_range_m=float(target_range_m),
        tolerance_m=float(tolerance_m),
        longitude_step_deg=float(longitude_step_deg),
        latitude_step_deg=float(latitude_step_deg),
        points=tuple(points),
    )
