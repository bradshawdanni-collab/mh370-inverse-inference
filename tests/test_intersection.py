import pytest

from mh370_inverse_inference.satcom.geometry import slant_range_m
from mh370_inverse_inference.satcom.intersection import (
    slant_range_residual_m,
    solve_latitudes_for_longitude,
)
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint, geodetic_to_ecef


def test_solver_recovers_known_surface_point() -> None:
    satellite = geodetic_to_ecef(
        GeodeticPoint(latitude_deg=0.0, longitude_deg=64.5, altitude_m=35_786_000.0)
    )
    expected = GeodeticPoint(latitude_deg=-30.0, longitude_deg=90.0)
    target_range_m = slant_range_m(geodetic_to_ecef(expected), satellite)

    roots = solve_latitudes_for_longitude(
        longitude_deg=90.0,
        satellite_ecef=satellite,
        target_range_m=target_range_m,
        latitude_step_deg=2.0,
        tolerance_m=0.1,
    )

    assert any(root.latitude_deg == pytest.approx(-30.0, abs=1e-5) for root in roots)
    assert all(abs(root.residual_m) <= 0.1 for root in roots)


def test_residual_is_zero_for_matching_range() -> None:
    satellite = geodetic_to_ecef(
        GeodeticPoint(latitude_deg=0.0, longitude_deg=64.5, altitude_m=35_786_000.0)
    )
    point = GeodeticPoint(latitude_deg=-20.0, longitude_deg=100.0)
    target_range_m = slant_range_m(geodetic_to_ecef(point), satellite)

    residual = slant_range_residual_m(
        point,
        satellite_ecef=satellite,
        target_range_m=target_range_m,
    )
    assert residual == pytest.approx(0.0, abs=1e-9)


def test_invalid_target_range_is_rejected() -> None:
    satellite = geodetic_to_ecef(
        GeodeticPoint(latitude_deg=0.0, longitude_deg=64.5, altitude_m=35_786_000.0)
    )
    with pytest.raises(ValueError):
        solve_latitudes_for_longitude(
            longitude_deg=90.0,
            satellite_ecef=satellite,
            target_range_m=0.0,
        )
