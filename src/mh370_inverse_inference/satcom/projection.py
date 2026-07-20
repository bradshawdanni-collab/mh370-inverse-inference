"""Fail-closed sphere intersections with WGS84 geodetic-height surfaces."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    ecef_distance_m,
    geodetic_to_ecef,
    normalize_longitude_deg,
)

SURFACE_MODEL_ID: Final = "WGS84_GEODETIC_HEIGHT"
BRANCH_RULE_ID: Final = "LOWER_LATITUDE_ROOT"
ROOT_SOLVER_ID: Final = "BRACKETED_BISECTION_FAIL_CLOSED"
POINT_PAIRING_RULE_ID: Final = "SAME_LONGITUDE"
ENDPOINT_POLICY_ID: Final = "EXCLUDE_TANGENCY_NEIGHBOURHOOD"


@dataclass(frozen=True, slots=True)
class LongitudeSphereIntersection:
    """Two ordered latitude roots at one longitude and geodetic height."""

    longitude_deg: float
    altitude_m: float
    lower_point: GeodeticPoint
    upper_point: GeodeticPoint

    def __post_init__(self) -> None:
        _require_canonical_longitude(self.longitude_deg)
        _require_finite(self.altitude_m, "altitude_m")
        if type(self.lower_point) is not GeodeticPoint:
            raise TypeError("lower_point must be GeodeticPoint")
        if type(self.upper_point) is not GeodeticPoint:
            raise TypeError("upper_point must be GeodeticPoint")
        for point, name in (
            (self.lower_point, "lower_point"),
            (self.upper_point, "upper_point"),
        ):
            if point.longitude_deg != self.longitude_deg:
                raise ValueError(f"{name} must use the declared longitude")
            if point.altitude_m != self.altitude_m:
                raise ValueError(f"{name} must use the declared altitude")
        if self.lower_point.latitude_deg >= self.upper_point.latitude_deg:
            raise ValueError("lower_point must have lower latitude than upper_point")


@dataclass(frozen=True, slots=True)
class SameLongitudeAltitudeShift:
    """Horizontal separation between lower roots on two height surfaces."""

    longitude_deg: float
    source_altitude_m: float
    target_altitude_m: float
    source_point: GeodeticPoint
    target_point: GeodeticPoint
    horizontal_shift_m: float

    def __post_init__(self) -> None:
        _require_canonical_longitude(self.longitude_deg)
        _require_finite(self.source_altitude_m, "source_altitude_m")
        _require_finite(self.target_altitude_m, "target_altitude_m")
        if self.source_altitude_m == self.target_altitude_m:
            raise ValueError("source and target altitudes must differ")
        if type(self.source_point) is not GeodeticPoint:
            raise TypeError("source_point must be GeodeticPoint")
        if type(self.target_point) is not GeodeticPoint:
            raise TypeError("target_point must be GeodeticPoint")
        if self.source_point.longitude_deg != self.longitude_deg:
            raise ValueError("source_point must use the declared longitude")
        if self.target_point.longitude_deg != self.longitude_deg:
            raise ValueError("target_point must use the declared longitude")
        if self.source_point.altitude_m != self.source_altitude_m:
            raise ValueError("source_point must use source_altitude_m")
        if self.target_point.altitude_m != self.target_altitude_m:
            raise ValueError("target_point must use target_altitude_m")
        _require_non_negative_finite(self.horizontal_shift_m, "horizontal_shift_m")
        expected = geodesic_distance_m(self.source_point, self.target_point)
        if self.horizontal_shift_m != expected:
            raise ValueError("horizontal_shift_m must match the paired points")


def solve_sphere_wgs84_intersection_at_longitude(
    satellite_position: ECEFPoint,
    target_range_m: float,
    *,
    longitude_deg: float,
    altitude_m: float,
    latitude_step_deg: float = 0.25,
    residual_tolerance_m: float = 0.001,
    maximum_iterations: int = 80,
    minimum_root_separation_deg: float = 0.01,
) -> LongitudeSphereIntersection:
    """Solve two bracketed WGS84 geodetic-height roots at one longitude."""
    if type(satellite_position) is not ECEFPoint:
        raise TypeError("satellite_position must be ECEFPoint")
    _require_positive_finite(target_range_m, "target_range_m")
    _require_canonical_longitude(longitude_deg)
    longitude_deg = normalize_longitude_deg(longitude_deg)
    _require_finite(altitude_m, "altitude_m")
    _require_positive_finite(latitude_step_deg, "latitude_step_deg")
    if latitude_step_deg > 1.0:
        raise ValueError("latitude_step_deg must not exceed 1 degree")
    _require_positive_finite(residual_tolerance_m, "residual_tolerance_m")
    _require_positive_finite(
        minimum_root_separation_deg,
        "minimum_root_separation_deg",
    )
    if type(maximum_iterations) is not int:
        raise TypeError("maximum_iterations must be int")
    if maximum_iterations <= 0:
        raise ValueError("maximum_iterations must be greater than zero")

    latitudes = _latitude_axis(latitude_step_deg)
    residuals = tuple(
        _range_residual_m(
            satellite_position,
            target_range_m,
            latitude_deg=latitude,
            longitude_deg=longitude_deg,
            altitude_m=altitude_m,
        )
        for latitude in latitudes
    )
    roots: list[float] = []

    paired_values = zip(latitudes, residuals, strict=True)
    for index, (latitude, residual) in enumerate(paired_values):
        if abs(residual) <= residual_tolerance_m:
            _append_unique_root(roots, latitude)
        if index == 0:
            continue
        previous_latitude = latitudes[index - 1]
        previous_residual = residuals[index - 1]
        if (
            abs(previous_residual) > residual_tolerance_m
            and abs(residual) > residual_tolerance_m
            and previous_residual * residual < 0.0
        ):
            root = _bisect_latitude_root(
                satellite_position,
                target_range_m,
                longitude_deg=longitude_deg,
                altitude_m=altitude_m,
                lower_latitude_deg=previous_latitude,
                upper_latitude_deg=latitude,
                lower_residual_m=previous_residual,
                residual_tolerance_m=residual_tolerance_m,
                maximum_iterations=maximum_iterations,
            )
            _append_unique_root(roots, root)

    if len(roots) != 2:
        raise ValueError(
            "exactly two bracketed roots are required; "
            "no-intersection and tangency neighborhoods fail closed"
        )
    roots.sort()
    if roots[1] - roots[0] < minimum_root_separation_deg:
        raise ValueError(
            "root separation falls within the excluded tangency neighborhood"
        )

    lower_point = GeodeticPoint(roots[0], longitude_deg, altitude_m)
    upper_point = GeodeticPoint(roots[1], longitude_deg, altitude_m)
    for point in (lower_point, upper_point):
        residual = _range_residual_m(
            satellite_position,
            target_range_m,
            latitude_deg=point.latitude_deg,
            longitude_deg=point.longitude_deg,
            altitude_m=point.altitude_m,
        )
        if abs(residual) > residual_tolerance_m:
            raise ValueError("intersection residual exceeds residual_tolerance_m")

    return LongitudeSphereIntersection(
        longitude_deg=longitude_deg,
        altitude_m=altitude_m,
        lower_point=lower_point,
        upper_point=upper_point,
    )


def compare_lower_branch_altitudes_at_longitude(
    satellite_position: ECEFPoint,
    target_range_m: float,
    *,
    longitude_deg: float,
    source_altitude_m: float,
    target_altitude_m: float,
    latitude_step_deg: float = 0.25,
    residual_tolerance_m: float = 0.001,
    maximum_iterations: int = 80,
    minimum_root_separation_deg: float = 0.01,
) -> SameLongitudeAltitudeShift:
    """Compare lower-latitude roots using exact same-longitude pairing."""
    _require_canonical_longitude(longitude_deg)
    longitude_deg = normalize_longitude_deg(longitude_deg)

    source = solve_sphere_wgs84_intersection_at_longitude(
        satellite_position,
        target_range_m,
        longitude_deg=longitude_deg,
        altitude_m=source_altitude_m,
        latitude_step_deg=latitude_step_deg,
        residual_tolerance_m=residual_tolerance_m,
        maximum_iterations=maximum_iterations,
        minimum_root_separation_deg=minimum_root_separation_deg,
    )
    target = solve_sphere_wgs84_intersection_at_longitude(
        satellite_position,
        target_range_m,
        longitude_deg=longitude_deg,
        altitude_m=target_altitude_m,
        latitude_step_deg=latitude_step_deg,
        residual_tolerance_m=residual_tolerance_m,
        maximum_iterations=maximum_iterations,
        minimum_root_separation_deg=minimum_root_separation_deg,
    )
    shift_m = geodesic_distance_m(source.lower_point, target.lower_point)
    return SameLongitudeAltitudeShift(
        longitude_deg=longitude_deg,
        source_altitude_m=source_altitude_m,
        target_altitude_m=target_altitude_m,
        source_point=source.lower_point,
        target_point=target.lower_point,
        horizontal_shift_m=shift_m,
    )


def _latitude_axis(step_deg: float) -> tuple[float, ...]:
    values = [-90.0]
    latitude = -90.0 + step_deg
    while latitude < 90.0:
        values.append(latitude)
        latitude += step_deg
    values.append(90.0)
    return tuple(values)


def _range_residual_m(
    satellite_position: ECEFPoint,
    target_range_m: float,
    *,
    latitude_deg: float,
    longitude_deg: float,
    altitude_m: float,
) -> float:
    point = geodetic_to_ecef(
        GeodeticPoint(
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            altitude_m=altitude_m,
        )
    )
    return ecef_distance_m(point, satellite_position) - target_range_m


def _bisect_latitude_root(
    satellite_position: ECEFPoint,
    target_range_m: float,
    *,
    longitude_deg: float,
    altitude_m: float,
    lower_latitude_deg: float,
    upper_latitude_deg: float,
    lower_residual_m: float,
    residual_tolerance_m: float,
    maximum_iterations: int,
) -> float:
    lower = lower_latitude_deg
    upper = upper_latitude_deg
    lower_residual = lower_residual_m

    for _ in range(maximum_iterations):
        midpoint = (lower + upper) / 2.0
        midpoint_residual = _range_residual_m(
            satellite_position,
            target_range_m,
            latitude_deg=midpoint,
            longitude_deg=longitude_deg,
            altitude_m=altitude_m,
        )
        if abs(midpoint_residual) <= residual_tolerance_m:
            return midpoint
        if math.copysign(1.0, midpoint_residual) == math.copysign(
            1.0,
            lower_residual,
        ):
            lower = midpoint
            lower_residual = midpoint_residual
        else:
            upper = midpoint

    midpoint = (lower + upper) / 2.0
    residual = _range_residual_m(
        satellite_position,
        target_range_m,
        latitude_deg=midpoint,
        longitude_deg=longitude_deg,
        altitude_m=altitude_m,
    )
    if abs(residual) > residual_tolerance_m:
        raise ValueError("bracketed root did not converge within maximum_iterations")
    return midpoint


def _append_unique_root(roots: list[float], latitude_deg: float) -> None:
    if not roots or all(abs(latitude_deg - root) > 1e-10 for root in roots):
        roots.append(latitude_deg)


def _require_canonical_longitude(value: float) -> None:
    _require_finite(value, "longitude_deg")
    if not -180.0 <= value < 180.0:
        raise ValueError("longitude_deg must be within [-180, 180)")


def _require_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def _require_positive_finite(value: float, name: str) -> None:
    _require_finite(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero")


def _require_non_negative_finite(value: float, name: str) -> None:
    _require_finite(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
