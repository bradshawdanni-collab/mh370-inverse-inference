"""Provisional numerical regressions for the seventh-arc projection contract."""

import json
from pathlib import Path

import pytest

from mh370_inverse_inference.satcom.projection import (
    BRANCH_RULE_ID,
    ENDPOINT_POLICY_ID,
    POINT_PAIRING_RULE_ID,
    ROOT_SOLVER_ID,
    SURFACE_MODEL_ID,
    compare_lower_branch_altitudes_at_longitude,
    solve_sphere_wgs84_intersection_at_longitude,
)
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    ecef_distance_m,
    geodetic_to_ecef,
)

_FIXTURE_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "satcom"
    / "provisional_seventh_arc_projection.json"
)
_FIXTURE = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
_GEOMETRY = _FIXTURE["provisional_geometry"]
_SATELLITE_VALUES = _GEOMETRY["satellite_ecef_m"]
_SATELLITE = ECEFPoint(
    x_m=float(_SATELLITE_VALUES["x"]),
    y_m=float(_SATELLITE_VALUES["y"]),
    z_m=float(_SATELLITE_VALUES["z"]),
)
_TARGET_RANGE_M = float(_GEOMETRY["satellite_aircraft_range_m"])
_SOLVER = _FIXTURE["solver_parameters"]


def _solver_kwargs() -> dict[str, float | int]:
    return {
        "latitude_step_deg": float(_SOLVER["latitude_step_deg"]),
        "residual_tolerance_m": float(_SOLVER["residual_tolerance_m"]),
        "maximum_iterations": int(_SOLVER["maximum_iterations"]),
        "minimum_root_separation_deg": float(
            _SOLVER["minimum_root_separation_deg"]
        ),
    }


def _range_residual_m(point: GeodeticPoint) -> float:
    return abs(
        ecef_distance_m(_SATELLITE, geodetic_to_ecef(point)) - _TARGET_RANGE_M
    )


def _checkpoint_id(checkpoint: dict[str, float]) -> str:
    return f"lon-{checkpoint['longitude_deg']:g}"


def test_provisional_fixture_preserves_non_authoritative_boundary() -> None:
    assert _FIXTURE["fixture_scope"] == "TEST_ONLY_NUMERICAL_REGRESSION"
    assert _FIXTURE["result_status"] == (
        "PROVISIONAL_PENDING_INDEPENDENT_REVIEW"
    )
    assert _FIXTURE["authoritative"] is False
    assert _FIXTURE["benchmark_fixture_generation"] == "prohibited"
    assert _FIXTURE["prohibited_repository_target"] == (
        "data/satcom/published/benchmark_fixture.csv"
    )
    assert _FIXTURE["physical_accuracy_claim"] == "NONE"


def test_fixture_contract_matches_projection_implementation() -> None:
    assert _FIXTURE["surface_model"] == SURFACE_MODEL_ID
    assert _FIXTURE["branch_rule"] == BRANCH_RULE_ID
    assert _FIXTURE["root_solver"] == "BRACKETED_FAIL_CLOSED"
    assert _FIXTURE["implementation_root_solver"] == ROOT_SOLVER_ID
    assert _FIXTURE["point_pairing_rule"] == POINT_PAIRING_RULE_ID
    assert _FIXTURE["endpoint_policy"] == ENDPOINT_POLICY_ID
    assert float(_FIXTURE["source_altitude_m"]) == 10_000.0
    assert float(_FIXTURE["target_altitude_m"]) == 0.0


@pytest.mark.parametrize(
    "checkpoint",
    _FIXTURE["checkpoints"],
    ids=_checkpoint_id,
)
def test_provisional_seventh_arc_checkpoint(
    checkpoint: dict[str, float],
) -> None:
    longitude_deg = float(checkpoint["longitude_deg"])
    source_altitude_m = float(_FIXTURE["source_altitude_m"])
    target_altitude_m = float(_FIXTURE["target_altitude_m"])
    solver_kwargs = _solver_kwargs()

    source = solve_sphere_wgs84_intersection_at_longitude(
        _SATELLITE,
        _TARGET_RANGE_M,
        longitude_deg=longitude_deg,
        altitude_m=source_altitude_m,
        **solver_kwargs,
    )
    target = solve_sphere_wgs84_intersection_at_longitude(
        _SATELLITE,
        _TARGET_RANGE_M,
        longitude_deg=longitude_deg,
        altitude_m=target_altitude_m,
        **solver_kwargs,
    )
    result = compare_lower_branch_altitudes_at_longitude(
        _SATELLITE,
        _TARGET_RANGE_M,
        longitude_deg=longitude_deg,
        source_altitude_m=source_altitude_m,
        target_altitude_m=target_altitude_m,
        **solver_kwargs,
    )
    replay = compare_lower_branch_altitudes_at_longitude(
        _SATELLITE,
        _TARGET_RANGE_M,
        longitude_deg=longitude_deg,
        source_altitude_m=source_altitude_m,
        target_altitude_m=target_altitude_m,
        **solver_kwargs,
    )

    source_roots = (source.lower_point, source.upper_point)
    target_roots = (target.lower_point, target.upper_point)
    assert len(source_roots) == len(target_roots) == 2
    assert source.lower_point.latitude_deg < source.upper_point.latitude_deg
    assert target.lower_point.latitude_deg < target.upper_point.latitude_deg

    minimum_separation = float(_SOLVER["minimum_root_separation_deg"])
    assert (
        source.upper_point.latitude_deg - source.lower_point.latitude_deg
        >= minimum_separation
    )
    assert (
        target.upper_point.latitude_deg - target.lower_point.latitude_deg
        >= minimum_separation
    )

    residual_tolerance_m = float(_SOLVER["residual_tolerance_m"])
    for point in source_roots + target_roots:
        assert _range_residual_m(point) <= residual_tolerance_m

    assert result.source_point == source.lower_point
    assert result.target_point == target.lower_point
    assert result.source_point.longitude_deg == longitude_deg
    assert result.target_point.longitude_deg == longitude_deg
    assert result.target_point.latitude_deg > result.source_point.latitude_deg

    assert result.target_point.latitude_deg == pytest.approx(
        float(checkpoint["target_0m_lower_latitude_deg"]),
        abs=1e-8,
    )
    assert result.source_point.latitude_deg == pytest.approx(
        float(checkpoint["source_10000m_lower_latitude_deg"]),
        abs=1e-8,
    )
    assert result.horizontal_shift_m == pytest.approx(
        float(checkpoint["horizontal_shift_m"]),
        abs=float(_FIXTURE["numerical_regression_tolerance_m"]),
    )
    assert result == replay


def test_minimum_shift_claim_is_limited_to_sampled_set() -> None:
    shifts: dict[float, float] = {}
    for checkpoint in _FIXTURE["checkpoints"]:
        longitude_deg = float(checkpoint["longitude_deg"])
        result = compare_lower_branch_altitudes_at_longitude(
            _SATELLITE,
            _TARGET_RANGE_M,
            longitude_deg=longitude_deg,
            source_altitude_m=float(_FIXTURE["source_altitude_m"]),
            target_altitude_m=float(_FIXTURE["target_altitude_m"]),
            **_solver_kwargs(),
        )
        shifts[longitude_deg] = result.horizontal_shift_m

    assert min(shifts, key=shifts.__getitem__) == 64.4644
    assert _FIXTURE["minimum_shift_claim_scope"] == (
        "WITHIN_THIS_SAMPLED_SET_ONLY"
    )
