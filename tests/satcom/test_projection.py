"""Tests for fail-closed WGS84 geodetic-height sphere intersections."""

import math

import pytest

from mh370_inverse_inference.satcom.projection import (
    BRANCH_RULE_ID,
    ENDPOINT_POLICY_ID,
    POINT_PAIRING_RULE_ID,
    ROOT_SOLVER_ID,
    SURFACE_MODEL_ID,
    SameLongitudeAltitudeShift,
    compare_lower_branch_altitudes_at_longitude,
    solve_sphere_wgs84_intersection_at_longitude,
)
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    ecef_distance_m,
    geodetic_to_ecef,
)

_SATELLITE = ECEFPoint(42_164_000.0, 0.0, 0.0)


def _range_to(latitude_deg: float, altitude_m: float = 0.0) -> float:
    return ecef_distance_m(
        _SATELLITE,
        geodetic_to_ecef(GeodeticPoint(latitude_deg, 0.0, altitude_m)),
    )


def test_projection_contract_identifiers_are_explicit() -> None:
    assert SURFACE_MODEL_ID == "WGS84_GEODETIC_HEIGHT"
    assert BRANCH_RULE_ID == "LOWER_LATITUDE_ROOT"
    assert ROOT_SOLVER_ID == "BRACKETED_BISECTION_FAIL_CLOSED"
    assert POINT_PAIRING_RULE_ID == "SAME_LONGITUDE"
    assert ENDPOINT_POLICY_ID == "EXCLUDE_TANGENCY_NEIGHBOURHOOD"


def test_solver_recovers_ordered_symmetric_roots() -> None:
    result = solve_sphere_wgs84_intersection_at_longitude(
        _SATELLITE,
        _range_to(30.0),
        longitude_deg=0.0,
        altitude_m=0.0,
    )

    assert result.lower_point.latitude_deg == pytest.approx(-30.0, abs=1e-8)
    assert result.upper_point.latitude_deg == pytest.approx(30.0, abs=1e-8)
    assert result.lower_point.longitude_deg == 0.0
    assert result.upper_point.longitude_deg == 0.0
    assert result.lower_point.altitude_m == 0.0
    assert result.upper_point.altitude_m == 0.0


def test_solver_is_deterministic() -> None:
    arguments = {
        "longitude_deg": 0.0,
        "altitude_m": 0.0,
    }
    first = solve_sphere_wgs84_intersection_at_longitude(
        _SATELLITE,
        _range_to(30.0),
        **arguments,
    )
    second = solve_sphere_wgs84_intersection_at_longitude(
        _SATELLITE,
        _range_to(30.0),
        **arguments,
    )

    assert first == second


def test_same_longitude_altitude_comparison_uses_lower_branch() -> None:
    target_range_m = _range_to(-30.0, 10_000.0)

    result = compare_lower_branch_altitudes_at_longitude(
        _SATELLITE,
        target_range_m,
        longitude_deg=0.0,
        source_altitude_m=10_000.0,
        target_altitude_m=0.0,
    )

    assert result.source_point.latitude_deg == pytest.approx(-30.0, abs=1e-8)
    assert result.target_point.latitude_deg > result.source_point.latitude_deg
    assert result.source_point.longitude_deg == result.target_point.longitude_deg == 0.0
    assert result.horizontal_shift_m > 0.0


def test_solver_excludes_tangency_neighborhood() -> None:
    with pytest.raises(ValueError, match="exactly two bracketed roots"):
        solve_sphere_wgs84_intersection_at_longitude(
            _SATELLITE,
            _range_to(0.0),
            longitude_deg=0.0,
            altitude_m=0.0,
        )


def test_solver_fails_closed_when_no_intersection_exists() -> None:
    with pytest.raises(ValueError, match="exactly two bracketed roots"):
        solve_sphere_wgs84_intersection_at_longitude(
            _SATELLITE,
            1.0,
            longitude_deg=0.0,
            altitude_m=0.0,
        )


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("target_range_m", 0.0, "greater than zero"),
        ("longitude_deg", 180.0, "within"),
        ("altitude_m", math.inf, "finite"),
        ("latitude_step_deg", 2.0, "must not exceed"),
        ("residual_tolerance_m", 0.0, "greater than zero"),
        ("minimum_root_separation_deg", 0.0, "greater than zero"),
    ],
)
def test_solver_rejects_invalid_numeric_contracts(
    name: str,
    value: float,
    message: str,
) -> None:
    kwargs = {
        "longitude_deg": 0.0,
        "altitude_m": 0.0,
        "latitude_step_deg": 0.25,
        "residual_tolerance_m": 0.001,
        "minimum_root_separation_deg": 0.01,
    }
    target_range_m = _range_to(30.0)
    if name == "target_range_m":
        target_range_m = value
    else:
        kwargs[name] = value

    with pytest.raises(ValueError, match=message):
        solve_sphere_wgs84_intersection_at_longitude(
            _SATELLITE,
            target_range_m,
            **kwargs,
        )


def test_solver_rejects_non_ecef_satellite() -> None:
    with pytest.raises(TypeError, match="ECEFPoint"):
        solve_sphere_wgs84_intersection_at_longitude(
            GeodeticPoint(0.0, 0.0, 0.0),  # type: ignore[arg-type]
            _range_to(30.0),
            longitude_deg=0.0,
            altitude_m=0.0,
        )


def test_shift_contract_rejects_inconsistent_metric() -> None:
    source = GeodeticPoint(-30.0, 0.0, 10_000.0)
    target = GeodeticPoint(-29.9, 0.0, 0.0)

    with pytest.raises(ValueError, match="must match"):
        SameLongitudeAltitudeShift(
            longitude_deg=0.0,
            source_altitude_m=10_000.0,
            target_altitude_m=0.0,
            source_point=source,
            target_point=target,
            horizontal_shift_m=0.0,
        )
