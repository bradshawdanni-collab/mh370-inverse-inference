"""Tests for deterministic slant-range calculations."""

from __future__ import annotations

import pytest

from mh370_inverse_inference.satcom import satellite, slant_range, wgs84


def test_equatorial_reference_range() -> None:
    point = wgs84.ECEFPoint(wgs84.WGS84_A_M, 0.0, 0.0)
    position = satellite.SatellitePosition(
        epoch_utc="epoch-1",
        ecef=wgs84.ECEFPoint(wgs84.WGS84_A_M + 35_786_000.0, 0.0, 0.0),
    )

    assert slant_range.slant_range_m(point, position) == 35_786_000.0


def test_polar_reference_range() -> None:
    point = wgs84.ECEFPoint(0.0, 0.0, wgs84.WGS84_B_M)
    position = satellite.SatellitePosition(
        epoch_utc="epoch-1",
        ecef=wgs84.ECEFPoint(0.0, 0.0, wgs84.WGS84_B_M + 1_000.0),
    )

    assert slant_range.slant_range_m(point, position) == 1_000.0


def test_range_matches_underlying_ecef_distance() -> None:
    point = wgs84.ECEFPoint(1.0, 2.0, 3.0)
    position = satellite.SatellitePosition(
        epoch_utc="epoch-1",
        ecef=wgs84.ECEFPoint(4.0, 6.0, 3.0),
    )

    expected = wgs84.ecef_distance_m(point, position.ecef)

    assert slant_range.slant_range_m(point, position) == expected
    assert expected == wgs84.ecef_distance_m(position.ecef, point)


def test_zero_distance_is_supported() -> None:
    point = wgs84.ECEFPoint(1.0, 2.0, 3.0)
    position = satellite.SatellitePosition(epoch_utc="epoch-1", ecef=point)

    assert slant_range.slant_range_m(point, position) == 0.0


def test_invalid_input_types_are_rejected() -> None:
    point = wgs84.ECEFPoint(1.0, 2.0, 3.0)
    position = satellite.SatellitePosition(
        epoch_utc="epoch-1",
        ecef=wgs84.ECEFPoint(4.0, 5.0, 6.0),
    )

    with pytest.raises(TypeError, match="point"):
        slant_range.slant_range_m(position, position)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="satellite"):
        slant_range.slant_range_m(point, point)  # type: ignore[arg-type]
