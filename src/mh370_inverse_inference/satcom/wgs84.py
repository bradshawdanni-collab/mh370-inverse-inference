"""WGS84 constants and geodetic/ECEF coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt

WGS84_A_M: float = 6_378_137.0
WGS84_F: float = 1.0 / 298.257_223_563
WGS84_B_M: float = WGS84_A_M * (1.0 - WGS84_F)
WGS84_E2: float = WGS84_F * (2.0 - WGS84_F)


@dataclass(frozen=True, slots=True)
class ECEFPoint:
    """Earth-centred, Earth-fixed Cartesian coordinate in metres."""

    x_m: float
    y_m: float
    z_m: float


@dataclass(frozen=True, slots=True)
class GeodeticPoint:
    """WGS84 geodetic coordinate."""

    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0


def geodetic_to_ecef(point: GeodeticPoint) -> ECEFPoint:
    """Convert a WGS84 geodetic point to ECEF coordinates."""
    latitude = radians(point.latitude_deg)
    longitude = radians(point.longitude_deg)
    sin_lat = sin(latitude)
    cos_lat = cos(latitude)
    prime_vertical_radius = WGS84_A_M / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)

    x_m = (prime_vertical_radius + point.altitude_m) * cos_lat * cos(longitude)
    y_m = (prime_vertical_radius + point.altitude_m) * cos_lat * sin(longitude)
    z_m = (prime_vertical_radius * (1.0 - WGS84_E2) + point.altitude_m) * sin_lat
    return ECEFPoint(x_m=x_m, y_m=y_m, z_m=z_m)


def ecef_to_geodetic(point: ECEFPoint, *, max_iterations: int = 15) -> GeodeticPoint:
    """Convert ECEF coordinates to a WGS84 geodetic point.

    The iterative latitude solution converges rapidly for ordinary Earth and
    near-Earth positions. A deterministic iteration cap is used for auditability.
    """
    longitude = atan2(point.y_m, point.x_m)
    horizontal = sqrt(point.x_m * point.x_m + point.y_m * point.y_m)

    if horizontal == 0.0:
        latitude = 1.5707963267948966 if point.z_m >= 0.0 else -1.5707963267948966
        altitude_m = abs(point.z_m) - WGS84_B_M
        return GeodeticPoint(
            latitude_deg=latitude * 180.0 / 3.141592653589793,
            longitude_deg=0.0,
            altitude_m=altitude_m,
        )

    latitude = atan2(point.z_m, horizontal * (1.0 - WGS84_E2))
    altitude_m = 0.0

    for _ in range(max_iterations):
        sin_lat = sin(latitude)
        prime_vertical_radius = WGS84_A_M / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        altitude_m = horizontal / cos(latitude) - prime_vertical_radius
        ratio = WGS84_E2 * prime_vertical_radius / (prime_vertical_radius + altitude_m)
        denominator = horizontal * (1.0 - ratio)
        updated_latitude = atan2(point.z_m, denominator)
        if abs(updated_latitude - latitude) < 1e-12:
            latitude = updated_latitude
            break
        latitude = updated_latitude

    return GeodeticPoint(
        latitude_deg=latitude * 180.0 / 3.141592653589793,
        longitude_deg=longitude * 180.0 / 3.141592653589793,
        altitude_m=altitude_m,
    )
