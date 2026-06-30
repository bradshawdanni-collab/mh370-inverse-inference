"""WGS84 ellipsoid and satellite slant-range intersection helpers."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.satcom.geometry import slant_range_m
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint, geodetic_to_ecef


@dataclass(frozen=True, slots=True)
class LatitudeRoot:
    """One latitude solution for a fixed longitude and target slant range."""

    longitude_deg: float
    latitude_deg: float
    residual_m: float


def slant_range_residual_m(
    point: GeodeticPoint,
    *,
    satellite_ecef: object,
    target_range_m: float,
) -> float:
    """Return modelled minus target slant range in metres."""
    return slant_range_m(geodetic_to_ecef(point), satellite_ecef) - target_range_m


def _bisect_latitude(
    *,
    longitude_deg: float,
    lower_latitude_deg: float,
    upper_latitude_deg: float,
    satellite_ecef: object,
    target_range_m: float,
    altitude_m: float,
    tolerance_m: float,
    max_iterations: int,
) -> LatitudeRoot:
    lower = lower_latitude_deg
    upper = upper_latitude_deg
    lower_residual = slant_range_residual_m(
        GeodeticPoint(lower, longitude_deg, altitude_m),
        satellite_ecef=satellite_ecef,
        target_range_m=target_range_m,
    )

    for _ in range(max_iterations):
        midpoint = (lower + upper) / 2.0
        midpoint_residual = slant_range_residual_m(
            GeodeticPoint(midpoint, longitude_deg, altitude_m),
            satellite_ecef=satellite_ecef,
            target_range_m=target_range_m,
        )
        if abs(midpoint_residual) <= tolerance_m:
            return LatitudeRoot(longitude_deg, midpoint, midpoint_residual)
        if lower_residual * midpoint_residual <= 0.0:
            upper = midpoint
        else:
            lower = midpoint
            lower_residual = midpoint_residual

    midpoint = (lower + upper) / 2.0
    residual = slant_range_residual_m(
        GeodeticPoint(midpoint, longitude_deg, altitude_m),
        satellite_ecef=satellite_ecef,
        target_range_m=target_range_m,
    )
    return LatitudeRoot(longitude_deg, midpoint, residual)


def solve_latitudes_for_longitude(
    *,
    longitude_deg: float,
    satellite_ecef: object,
    target_range_m: float,
    altitude_m: float = 0.0,
    latitude_step_deg: float = 1.0,
    tolerance_m: float = 1.0,
    max_iterations: int = 80,
) -> tuple[LatitudeRoot, ...]:
    """Find all latitude roots for one longitude by bracketed bisection."""
    if target_range_m <= 0.0:
        raise ValueError("target_range_m must be positive")
    if latitude_step_deg <= 0.0 or latitude_step_deg > 30.0:
        raise ValueError("latitude_step_deg must be in (0, 30]")

    roots: list[LatitudeRoot] = []
    lower = -90.0
    lower_residual = slant_range_residual_m(
        GeodeticPoint(lower, longitude_deg, altitude_m),
        satellite_ecef=satellite_ecef,
        target_range_m=target_range_m,
    )

    while lower < 90.0:
        upper = min(90.0, lower + latitude_step_deg)
        upper_residual = slant_range_residual_m(
            GeodeticPoint(upper, longitude_deg, altitude_m),
            satellite_ecef=satellite_ecef,
            target_range_m=target_range_m,
        )
        if lower_residual == 0.0:
            roots.append(LatitudeRoot(longitude_deg, lower, 0.0))
        elif lower_residual * upper_residual < 0.0:
            roots.append(
                _bisect_latitude(
                    longitude_deg=longitude_deg,
                    lower_latitude_deg=lower,
                    upper_latitude_deg=upper,
                    satellite_ecef=satellite_ecef,
                    target_range_m=target_range_m,
                    altitude_m=altitude_m,
                    tolerance_m=tolerance_m,
                    max_iterations=max_iterations,
                )
            )
        lower = upper
        lower_residual = upper_residual

    return tuple(roots)
