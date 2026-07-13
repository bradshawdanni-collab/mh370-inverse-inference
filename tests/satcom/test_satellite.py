"""Tests for validated satellite-position primitives."""

from __future__ import annotations

import math

import pytest

from mh370_inverse_inference.satcom import satellite, wgs84


def test_satellite_position_is_immutable() -> None:
    position = satellite.SatellitePosition(
        epoch_utc="epoch-1",
        ecef=wgs84.ECEFPoint(42_164_000.0, 0.0, 0.0),
    )

    with pytest.raises(AttributeError):
        position.epoch_utc = "changed"  # type: ignore[misc]


def test_satellite_position_rejects_origin() -> None:
    with pytest.raises(ValueError, match="origin"):
        satellite.SatellitePosition(
            epoch_utc="epoch-1",
            ecef=wgs84.ECEFPoint(0.0, 0.0, 0.0),
        )


def test_satellite_position_rejects_invalid_metadata() -> None:
    valid_ecef = wgs84.ECEFPoint(42_164_000.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="empty"):
        satellite.SatellitePosition(epoch_utc="   ", ecef=valid_ecef)
    with pytest.raises(TypeError, match="str"):
        satellite.SatellitePosition(
            epoch_utc=1,  # type: ignore[arg-type]
            ecef=valid_ecef,
        )


def test_satellite_position_rejects_non_finite_coordinates() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="finite"):
            satellite.SatellitePosition(
                epoch_utc="epoch-1",
                ecef=wgs84.ECEFPoint(value, 0.0, 0.0),
            )


def test_geodetic_constructor_supports_reference_cases() -> None:
    equatorial = satellite.SatellitePosition.from_geodetic(
        epoch_utc="epoch-1",
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_m=35_786_000.0,
    )
    polar = satellite.SatellitePosition.from_geodetic(
        epoch_utc="epoch-1",
        latitude_deg=90.0,
        longitude_deg=0.0,
        altitude_m=35_786_000.0,
    )

    assert equatorial.ecef.x_m > wgs84.WGS84_A_M
    assert equatorial.ecef.z_m == pytest.approx(0.0, abs=1e-6)
    assert polar.ecef.z_m > wgs84.WGS84_B_M
