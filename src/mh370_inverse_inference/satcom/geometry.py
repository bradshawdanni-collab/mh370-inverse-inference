"""Deterministic SATCOM geometry primitives."""

from __future__ import annotations

from math import sqrt

from pyproj import Geod

from mh370_inverse_inference.satcom.wgs84 import ECEFPoint, GeodeticPoint

_WGS84_GEOD = Geod(ellps="WGS84")


def slant_range_m(first: ECEFPoint, second: ECEFPoint) -> float:
    """Return Euclidean slant range between two ECEF points in metres."""
    dx = second.x_m - first.x_m
    dy = second.y_m - first.y_m
    dz = second.z_m - first.z_m
    return sqrt(dx * dx + dy * dy + dz * dz)


def geodesic_distance_m(first: GeodeticPoint, second: GeodeticPoint) -> float:
    """Return WGS84 ellipsoidal surface distance in metres."""
    _, _, distance_m = _WGS84_GEOD.inv(
        first.longitude_deg,
        first.latitude_deg,
        second.longitude_deg,
        second.latitude_deg,
    )
    return float(distance_m)


def geodesic_forward(
    origin: GeodeticPoint,
    *,
    azimuth_deg: float,
    distance_m: float,
) -> GeodeticPoint:
    """Project a WGS84 surface point by azimuth and distance."""
    longitude_deg, latitude_deg, _ = _WGS84_GEOD.fwd(
        origin.longitude_deg,
        origin.latitude_deg,
        azimuth_deg,
        distance_m,
    )
    return GeodeticPoint(
        latitude_deg=float(latitude_deg),
        longitude_deg=float(longitude_deg),
        altitude_m=origin.altitude_m,
    )
