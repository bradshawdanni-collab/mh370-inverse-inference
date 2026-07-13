"""Tests for deterministic WGS84 coordinate primitives."""

from __future__ import annotations

import math

import pytest

from mh370_inverse_inference.satcom import wgs84


def test_equator_and_pole_coordinates() -> None:
    equator = wgs84.geodetic_to_ecef(wgs84.GeodeticPoint(0.0, 0.0, 0.0))
    north_pole = wgs84.geodetic_to_ecef(wgs84.GeodeticPoint(90.0, 0.0, 0.0))

    assert equator.x_m == pytest.approx(wgs84.WGS84_A_M, abs=1e-9)
    assert equator.y_m == pytest.approx(0.0, abs=1e-9)
    assert equator.z_m == pytest.approx(0.0, abs=1e-9)
    assert north_pole.x_m == pytest.approx(0.0, abs=1e-6)
    assert north_pole.y_m == pytest.approx(0.0, abs=1e-9)
    assert north_pole.z_m == pytest.approx(wgs84.WGS84_B_M, abs=1e-6)


def test_geodetic_ecef_round_trip_is_stable() -> None:
    original = wgs84.GeodeticPoint(-37.8136, 144.9631, 125.0)

    recovered = wgs84.ecef_to_geodetic(wgs84.geodetic_to_ecef(original))

    assert recovered.latitude_deg == pytest.approx(original.latitude_deg, abs=1e-9)
    assert recovered.longitude_deg == pytest.approx(
        original.longitude_deg,
        abs=1e-9,
    )
    assert recovered.altitude_m == pytest.approx(original.altitude_m, abs=1e-5)


def test_longitude_normalization_is_deterministic() -> None:
    assert wgs84.normalize_longitude_deg(180.0) == -180.0
    assert wgs84.normalize_longitude_deg(540.0) == -180.0
    assert wgs84.normalize_longitude_deg(-181.0) == 179.0
    assert wgs84.GeodeticPoint(0.0, 181.0).longitude_deg == -179.0


def test_ecef_distance_is_symmetric_and_deterministic() -> None:
    left = wgs84.ECEFPoint(1.0, 2.0, 3.0)
    right = wgs84.ECEFPoint(4.0, 6.0, 3.0)

    assert wgs84.ecef_distance_m(left, right) == 5.0
    assert wgs84.ecef_distance_m(left, right) == wgs84.ecef_distance_m(right, left)


def test_polar_inverse_conversion() -> None:
    recovered = wgs84.ecef_to_geodetic(
        wgs84.ECEFPoint(0.0, 0.0, wgs84.WGS84_B_M + 10.0)
    )

    assert recovered.latitude_deg == 90.0
    assert recovered.longitude_deg == 0.0
    assert recovered.altitude_m == pytest.approx(10.0, abs=1e-9)


def test_invalid_values_fail_closed() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="finite"):
            wgs84.GeodeticPoint(value, 0.0)
        with pytest.raises(ValueError, match="finite"):
            wgs84.ECEFPoint(value, 0.0, 0.0)
        with pytest.raises(ValueError, match="finite"):
            wgs84.normalize_longitude_deg(value)

    with pytest.raises(ValueError, match="latitude_deg"):
        wgs84.GeodeticPoint(90.1, 0.0)
    with pytest.raises(ValueError, match="no unique"):
        wgs84.ecef_to_geodetic(wgs84.ECEFPoint(0.0, 0.0, 0.0))


def test_wrong_types_are_rejected() -> None:
    with pytest.raises(TypeError, match="GeodeticPoint"):
        wgs84.geodetic_to_ecef(wgs84.ECEFPoint(1.0, 2.0, 3.0))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ECEFPoint"):
        wgs84.ecef_to_geodetic(wgs84.GeodeticPoint(0.0, 0.0))  # type: ignore[arg-type]
