"""Geodesic arc generation utilities."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.satcom.geometry import geodesic_forward
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


@dataclass(frozen=True, slots=True)
class ArcBand:
    """Nominal geodesic arc with lower and upper uncertainty boundaries."""

    nominal: tuple[GeodeticPoint, ...]
    lower: tuple[GeodeticPoint, ...]
    upper: tuple[GeodeticPoint, ...]


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
