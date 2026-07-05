"""Geodesic and satellite slant-range arc generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from mh370_inverse_inference.satcom.geometry import (
    geodesic_forward,
    slant_range_m,
)
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    ecef_to_geodetic,
    geodetic_to_ecef,
)


@dataclass(frozen=True, slots=True)
class ArcBand:
    """Nominal geodesic arc with lower and upper uncertainty boundaries."""

    nominal: tuple[GeodeticPoint, ...]
    lower: tuple[GeodeticPoint, ...]
    upper: tuple[GeodeticPoint, ...]


@dataclass(frozen=True, slots=True)
class SlantRangeArc:
    """Closed constant-altitude arc and its signed slant-range residuals."""

    points: tuple[GeodeticPoint, ...]
    residuals_m: tuple[float, ...]


def generate_geodesic_circle(
    center: GeodeticPoint,
    *,
    radius_m: float,
    point_count: int = 360,
) -> tuple[GeodeticPoint, ...]:
    """Generate a closed WGS84 geodesic circle around ``center``.

    This utility produces an ellipsoidal line of constant surface distance. It
    does not itself convert BTO into radius; that measurement model remains a
    separate auditable step.
    """
    if radius_m < 0.0:
        raise ValueError("radius_m must be non-negative")
    if point_count < 4:
        raise ValueError("point_count must be at least 4")

    points = [
        geodesic_forward(
            center,
            azimuth_deg=index * 360.0 / point_count,
            distance_m=radius_m,
        )
        for index in range(point_count)
    ]
    points.append(points[0])
    return tuple(points)


def generate_arc_band(
    center: GeodeticPoint,
    *,
    nominal_radius_m: float,
    radial_uncertainty_m: float,
    point_count: int = 360,
) -> ArcBand:
    """Generate nominal, lower, and upper geodesic uncertainty boundaries."""
    if radial_uncertainty_m < 0.0:
        raise ValueError("radial_uncertainty_m must be non-negative")
    lower_radius_m = max(0.0, nominal_radius_m - radial_uncertainty_m)
    upper_radius_m = nominal_radius_m + radial_uncertainty_m
    return ArcBand(
        nominal=generate_geodesic_circle(
            center,
            radius_m=nominal_radius_m,
            point_count=point_count,
        ),
        lower=generate_geodesic_circle(
            center,
            radius_m=lower_radius_m,
            point_count=point_count,
        ),
        upper=generate_geodesic_circle(
            center,
            radius_m=upper_radius_m,
            point_count=point_count,
        ),
    )


def slant_range_residual_m(
    satellite_position: ECEFPoint,
    candidate: GeodeticPoint,
    *,
    target_slant_range_m: float,
) -> float:
    """Return candidate slant range minus target slant range in metres."""
    if not isfinite(target_slant_range_m) or target_slant_range_m < 0.0:
        raise ValueError("target_slant_range_m must be finite and non-negative")
    candidate_ecef = geodetic_to_ecef(candidate)
    return slant_range_m(satellite_position, candidate_ecef) - target_slant_range_m


def solve_slant_range_point(
    satellite_position: ECEFPoint,
    *,
    target_slant_range_m: float,
    azimuth_deg: float,
    candidate_altitude_m: float,
    tolerance_m: float = 1.0,
    max_surface_distance_m: float = 12_000_000.0,
    max_iterations: int = 80,
) -> tuple[GeodeticPoint, float]:
    """Solve the first outward WGS84 point matching a target slant range."""
    scalar_inputs = (
        satellite_position.x_m,
        satellite_position.y_m,
        satellite_position.z_m,
        target_slant_range_m,
        azimuth_deg,
        candidate_altitude_m,
        tolerance_m,
        max_surface_distance_m,
    )
    if not all(isfinite(value) for value in scalar_inputs):
        raise ValueError("Slant-range solver inputs must be finite")
    if target_slant_range_m < 0.0:
        raise ValueError("target_slant_range_m must be non-negative")
    if candidate_altitude_m < 0.0:
        raise ValueError("candidate_altitude_m must be non-negative")
    if tolerance_m <= 0.0:
        raise ValueError("tolerance_m must be positive")
    if max_surface_distance_m <= 0.0:
        raise ValueError("max_surface_distance_m must be positive")
    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive")

    satellite_geodetic = ecef_to_geodetic(satellite_position)
    origin = GeodeticPoint(
        latitude_deg=satellite_geodetic.latitude_deg,
        longitude_deg=satellite_geodetic.longitude_deg,
        altitude_m=candidate_altitude_m,
    )
    lower_distance_m = 0.0
    lower_residual_m = slant_range_residual_m(
        satellite_position,
        origin,
        target_slant_range_m=target_slant_range_m,
    )
    if abs(lower_residual_m) <= tolerance_m:
        return origin, lower_residual_m
    if lower_residual_m > 0.0:
        raise ValueError("Target slant range is below the nadir range")

    upper_distance_m = min(1_000.0, max_surface_distance_m)
    upper_point = geodesic_forward(
        origin,
        azimuth_deg=azimuth_deg,
        distance_m=upper_distance_m,
    )
    upper_residual_m = slant_range_residual_m(
        satellite_position,
        upper_point,
        target_slant_range_m=target_slant_range_m,
    )

    while upper_residual_m < 0.0 and upper_distance_m < max_surface_distance_m:
        lower_distance_m = upper_distance_m
        lower_residual_m = upper_residual_m
        upper_distance_m = min(upper_distance_m * 2.0, max_surface_distance_m)
        upper_point = geodesic_forward(
            origin,
            azimuth_deg=azimuth_deg,
            distance_m=upper_distance_m,
        )
        upper_residual_m = slant_range_residual_m(
            satellite_position,
            upper_point,
            target_slant_range_m=target_slant_range_m,
        )

    if upper_residual_m < 0.0:
        raise ValueError("Target slant range could not be bracketed")

    candidate = upper_point
    candidate_residual_m = upper_residual_m
    for _ in range(max_iterations):
        midpoint_m = (lower_distance_m + upper_distance_m) / 2.0
        candidate = geodesic_forward(
            origin,
            azimuth_deg=azimuth_deg,
            distance_m=midpoint_m,
        )
        candidate_residual_m = slant_range_residual_m(
            satellite_position,
            candidate,
            target_slant_range_m=target_slant_range_m,
        )
        if abs(candidate_residual_m) <= tolerance_m:
            return candidate, candidate_residual_m
        if candidate_residual_m < 0.0:
            lower_distance_m = midpoint_m
            lower_residual_m = candidate_residual_m
        else:
            upper_distance_m = midpoint_m
            upper_residual_m = candidate_residual_m

    raise ValueError(
        "Slant-range solver did not converge within the iteration limit"
    )


def generate_slant_range_arc(
    satellite_position: ECEFPoint,
    *,
    target_slant_range_m: float,
    candidate_altitude_m: float,
    point_count: int = 360,
    tolerance_m: float = 1.0,
    max_surface_distance_m: float = 12_000_000.0,
    max_iterations: int = 80,
) -> SlantRangeArc:
    """Generate a closed WGS84 candidate arc for one satellite slant range."""
    if point_count < 4:
        raise ValueError("point_count must be at least 4")

    solved = [
        solve_slant_range_point(
            satellite_position,
            target_slant_range_m=target_slant_range_m,
            azimuth_deg=index * 360.0 / point_count,
            candidate_altitude_m=candidate_altitude_m,
            tolerance_m=tolerance_m,
            max_surface_distance_m=max_surface_distance_m,
            max_iterations=max_iterations,
        )
        for index in range(point_count)
    ]
    points = [item[0] for item in solved]
    residuals_m = [item[1] for item in solved]
    points.append(points[0])
    residuals_m.append(residuals_m[0])
    return SlantRangeArc(points=tuple(points), residuals_m=tuple(residuals_m))
