"""Deterministic WGS84 coordinate primitives for the L0.0 SATCOM layer."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

WGS84_A_M: Final = 6_378_137.0
WGS84_F: Final = 1.0 / 298.257_223_563
WGS84_B_M: Final = WGS84_A_M * (1.0 - WGS84_F)
WGS84_E2: Final = WGS84_F * (2.0 - WGS84_F)
WGS84_EP2: Final = (WGS84_A_M**2 - WGS84_B_M**2) / WGS84_B_M**2


def _require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def normalize_longitude_deg(longitude_deg: float) -> float:
    """Normalize longitude to the half-open interval [-180, 180)."""
    _require_finite(longitude_deg, "longitude_deg")
    normalized = (longitude_deg + 180.0) % 360.0 - 180.0
    return 0.0 if normalized == -0.0 else normalized


@dataclass(frozen=True, slots=True)
class ECEFPoint:
    """Earth-centred, Earth-fixed Cartesian coordinate in metres."""

    x_m: float
    y_m: float
    z_m: float

    def __post_init__(self) -> None:
        _require_finite(self.x_m, "x_m")
        _require_finite(self.y_m, "y_m")
        _require_finite(self.z_m, "z_m")


@dataclass(frozen=True, slots=True)
class GeodeticPoint:
    """Validated WGS84 geodetic coordinate."""

    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0

    def __post_init__(self) -> None:
        _require_finite(self.latitude_deg, "latitude_deg")
        _require_finite(self.longitude_deg, "longitude_deg")
        _require_finite(self.altitude_m, "altitude_m")
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude_deg must be within [-90, 90]")
        object.__setattr__(
            self,
            "longitude_deg",
            normalize_longitude_deg(self.longitude_deg),
        )


def geodetic_to_ecef(point: GeodeticPoint) -> ECEFPoint:
    """Convert a validated WGS84 geodetic point to ECEF coordinates."""
    if type(point) is not GeodeticPoint:
        raise TypeError("point must be GeodeticPoint")

    latitude = math.radians(point.latitude_deg)
    longitude = math.radians(point.longitude_deg)
    sin_latitude = math.sin(latitude)
    cos_latitude = math.cos(latitude)
    prime_vertical_radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * sin_latitude**2)

    x_m = (
        (prime_vertical_radius + point.altitude_m) * cos_latitude * math.cos(longitude)
    )
    y_m = (
        (prime_vertical_radius + point.altitude_m) * cos_latitude * math.sin(longitude)
    )
    z_m = (prime_vertical_radius * (1.0 - WGS84_E2) + point.altitude_m) * sin_latitude
    return ECEFPoint(x_m=x_m, y_m=y_m, z_m=z_m)


def ecef_to_geodetic(point: ECEFPoint) -> GeodeticPoint:
    """Convert one validated ECEF point to geodetic form on WGS84."""
    if type(point) is not ECEFPoint:
        raise TypeError("point must be ECEFPoint")

    horizontal = math.hypot(point.x_m, point.y_m)
    if horizontal == 0.0 and point.z_m == 0.0:
        raise ValueError("the ECEF origin has no unique geodetic coordinate")

    longitude_deg = normalize_longitude_deg(
        math.degrees(math.atan2(point.y_m, point.x_m))
    )
    if horizontal == 0.0:
        latitude_deg = 90.0 if point.z_m > 0.0 else -90.0
        altitude_m = abs(point.z_m) - WGS84_B_M
        return GeodeticPoint(latitude_deg, longitude_deg, altitude_m)

    theta = math.atan2(
        point.z_m * WGS84_A_M,
        horizontal * WGS84_B_M,
    )
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    latitude = math.atan2(
        point.z_m + WGS84_EP2 * WGS84_B_M * sin_theta**3,
        horizontal - WGS84_E2 * WGS84_A_M * cos_theta**3,
    )

    sin_latitude = math.sin(latitude)
    prime_vertical_radius = WGS84_A_M / math.sqrt(1.0 - WGS84_E2 * sin_latitude**2)
    altitude_m = horizontal / math.cos(latitude) - prime_vertical_radius

    return GeodeticPoint(
        latitude_deg=math.degrees(latitude),
        longitude_deg=longitude_deg,
        altitude_m=altitude_m,
    )


def ecef_distance_m(left: ECEFPoint, right: ECEFPoint) -> float:
    """Return deterministic straight-line distance between two ECEF points."""
    if type(left) is not ECEFPoint or type(right) is not ECEFPoint:
        raise TypeError("left and right must be ECEFPoint values")
    return math.dist(
        (left.x_m, left.y_m, left.z_m),
        (right.x_m, right.y_m, right.z_m),
    )
