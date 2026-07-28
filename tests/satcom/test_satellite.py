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


PUBLISHED_START_POSITION = wgs84.ECEFPoint(
    x_m=18_177_500.0,
    y_m=38_051_700.0,
    z_m=440_000.0,
)
PUBLISHED_START_VELOCITY = satellite.ECEFVelocity(
    x_m_s=1.60,
    y_m_s=-1.51,
    z_m_s=-81.88,
)
PUBLISHED_END_POSITION = wgs84.ECEFPoint(
    x_m=18_178_400.0,
    y_m=38_050_800.0,
    z_m=390_500.0,
)
PUBLISHED_END_VELOCITY = satellite.ECEFVelocity(
    x_m_s=1.50,
    y_m_s=-1.58,
    z_m_s=-83.21,
)


def _interpolated_published_state(
    target_offset_s: float,
) -> satellite.SatelliteState:
    return satellite.interpolate_satellite_state_cubic_hermite(
        epoch_utc="2014-03-08T00:19:29.416Z",
        start_offset_s=0.0,
        target_offset_s=target_offset_s,
        end_offset_s=600.0,
        start_position=PUBLISHED_START_POSITION,
        start_velocity=PUBLISHED_START_VELOCITY,
        end_position=PUBLISHED_END_POSITION,
        end_velocity=PUBLISHED_END_VELOCITY,
    )


def test_cubic_hermite_interpolation_reproduces_endpoints() -> None:
    start = _interpolated_published_state(0.0)
    end = _interpolated_published_state(600.0)

    assert start.ecef == PUBLISHED_START_POSITION
    assert start.velocity == PUBLISHED_START_VELOCITY
    assert end.ecef == PUBLISHED_END_POSITION
    assert end.velocity == PUBLISHED_END_VELOCITY


def test_cubic_hermite_interpolation_matches_selected_epoch() -> None:
    state = _interpolated_published_state(569.416)

    assert state.ecef.x_m == pytest.approx(
        18_178_354.27195026,
        abs=1e-6,
    )
    assert state.ecef.y_m == pytest.approx(
        38_050_848.06484729,
        abs=1e-6,
    )
    assert state.ecef.z_m == pytest.approx(
        393_043.6546171822,
        abs=1e-6,
    )
    assert state.velocity.x_m_s == pytest.approx(
        1.4905848175466667,
        abs=1e-12,
    )
    assert state.velocity.y_m_s == pytest.approx(
        -1.5633706024564664,
        abs=1e-12,
    )
    assert state.velocity.z_m_s == pytest.approx(
        -83.12914420245867,
        abs=1e-12,
    )


@pytest.mark.parametrize("target_offset_s", [-0.001, 600.001])
def test_cubic_hermite_interpolation_rejects_extrapolation(
    target_offset_s: float,
) -> None:
    with pytest.raises(ValueError, match="within"):
        _interpolated_published_state(target_offset_s)


def test_cubic_hermite_interpolation_rejects_invalid_interval() -> None:
    with pytest.raises(ValueError, match="greater"):
        satellite.interpolate_satellite_state_cubic_hermite(
            epoch_utc="2014-03-08T00:19:29.416Z",
            start_offset_s=0.0,
            target_offset_s=0.0,
            end_offset_s=0.0,
            start_position=PUBLISHED_START_POSITION,
            start_velocity=PUBLISHED_START_VELOCITY,
            end_position=PUBLISHED_END_POSITION,
            end_velocity=PUBLISHED_END_VELOCITY,
        )
