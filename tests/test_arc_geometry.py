"""Tests for deterministic WGS84 slant-range candidate arcs."""

import pytest

from mh370_inverse_inference.satcom.arc import (
    generate_slant_range_arc,
    solve_slant_range_point,
)
from mh370_inverse_inference.satcom.geometry import geodesic_forward, slant_range_m
from mh370_inverse_inference.satcom.wgs84 import (
    GeodeticPoint,
    geodetic_to_ecef,
)


def _fixture_geometry() -> tuple[object, float, float]:
    satellite = geodetic_to_ecef(
        GeodeticPoint(
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=35_786_000.0,
        )
    )
    candidate_altitude_m = 10_000.0
    subpoint = GeodeticPoint(
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_m=candidate_altitude_m,
    )
    known_candidate = geodesic_forward(
        subpoint,
        azimuth_deg=90.0,
        distance_m=2_000_000.0,
    )
    target_range_m = slant_range_m(
        satellite,
        geodetic_to_ecef(known_candidate),
    )
    return satellite, candidate_altitude_m, target_range_m


def test_solver_recovers_requested_slant_range() -> None:
    satellite, candidate_altitude_m, target_range_m = _fixture_geometry()

    point, residual_m = solve_slant_range_point(
        satellite,
        target_slant_range_m=target_range_m,
        azimuth_deg=90.0,
        candidate_altitude_m=candidate_altitude_m,
        tolerance_m=0.1,
    )

    assert point.altitude_m == candidate_altitude_m
    assert abs(residual_m) <= 0.1
    assert slant_range_m(satellite, geodetic_to_ecef(point)) == pytest.approx(
        target_range_m,
        abs=0.1,
    )


def test_generated_arc_is_closed_and_matches_target_range() -> None:
    satellite, candidate_altitude_m, target_range_m = _fixture_geometry()

    arc = generate_slant_range_arc(
        satellite,
        target_slant_range_m=target_range_m,
        candidate_altitude_m=candidate_altitude_m,
        point_count=8,
        tolerance_m=0.5,
    )

    assert len(arc.points) == 9
    assert len(arc.residuals_m) == 9
    assert arc.points[0] == arc.points[-1]
    assert arc.residuals_m[0] == arc.residuals_m[-1]
    for point, residual_m in zip(arc.points, arc.residuals_m, strict=True):
        assert point.altitude_m == candidate_altitude_m
        assert abs(residual_m) <= 0.5
        assert slant_range_m(satellite, geodetic_to_ecef(point)) == pytest.approx(
            target_range_m,
            abs=0.5,
        )


def test_target_below_nadir_range_fails_closed() -> None:
    satellite, candidate_altitude_m, _ = _fixture_geometry()

    with pytest.raises(ValueError, match="below the nadir"):
        solve_slant_range_point(
            satellite,
            target_slant_range_m=1.0,
            azimuth_deg=0.0,
            candidate_altitude_m=candidate_altitude_m,
        )


def test_invalid_arc_point_count_fails_closed() -> None:
    satellite, candidate_altitude_m, target_range_m = _fixture_geometry()

    with pytest.raises(ValueError, match="point_count"):
        generate_slant_range_arc(
            satellite,
            target_slant_range_m=target_range_m,
            candidate_altitude_m=candidate_altitude_m,
            point_count=3,
        )
