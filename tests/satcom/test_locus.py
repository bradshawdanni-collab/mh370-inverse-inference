"""Tests for deterministic Earth-surface geometry."""

from __future__ import annotations

import math

import pytest

from mh370_inverse_inference.satcom import locus, satellite, slant_range, wgs84


def _reference_satellite() -> satellite.SatellitePosition:
    return satellite.SatellitePosition.from_geodetic(
        epoch_utc="epoch-1",
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_m=35_786_000.0,
    )


def test_surface_result_is_deterministic_and_valid() -> None:
    position = _reference_satellite()
    known = wgs84.geodetic_to_ecef(wgs84.GeodeticPoint(10.0, 0.0, 0.0))
    target = slant_range.slant_range_m(known, position)
    arguments = dict(
        tolerance_m=1.0,
        longitude_step_deg=10.0,
        latitude_step_deg=5.0,
        minimum_longitude_deg=-10.0,
        maximum_longitude_deg=10.0,
        minimum_latitude_deg=-20.0,
        maximum_latitude_deg=20.0,
    )

    first = locus.generate_surface_locus(position, target, **arguments)
    second = locus.generate_surface_locus(position, target, **arguments)

    assert first == second
    assert first.points
    assert any(
        point.geodetic.longitude_deg == 0.0
        and point.geodetic.latitude_deg == pytest.approx(10.0)
        for point in first.points
    )
    assert any(
        point.geodetic.longitude_deg == 0.0
        and point.geodetic.latitude_deg == pytest.approx(-10.0)
        for point in first.points
    )
    coordinates = tuple(
        (point.geodetic.longitude_deg, point.geodetic.latitude_deg)
        for point in first.points
    )
    assert coordinates == tuple(sorted(coordinates))
    for point in first.points:
        assert point.geodetic.altitude_m == 0.0
        assert point.ecef == wgs84.geodetic_to_ecef(point.geodetic)
        assert abs(slant_range.slant_range_m(point.ecef, position) - target) <= 1.0


def test_tangent_sample_is_emitted() -> None:
    position = _reference_satellite()
    surface = wgs84.geodetic_to_ecef(wgs84.GeodeticPoint(0.0, 0.0, 0.0))
    target = slant_range.slant_range_m(surface, position)

    result = locus.generate_surface_locus(
        position,
        target,
        tolerance_m=0.01,
        longitude_step_deg=10.0,
        latitude_step_deg=10.0,
        minimum_longitude_deg=-10.0,
        maximum_longitude_deg=10.0,
        minimum_latitude_deg=-10.0,
        maximum_latitude_deg=10.0,
    )

    assert any(
        point.geodetic.latitude_deg == 0.0
        and point.geodetic.longitude_deg == 0.0
        for point in result.points
    )


def test_no_solution_returns_empty_result() -> None:
    result = locus.generate_surface_locus(
        _reference_satellite(),
        1.0,
        longitude_step_deg=30.0,
        latitude_step_deg=30.0,
        minimum_longitude_deg=-30.0,
        maximum_longitude_deg=30.0,
        minimum_latitude_deg=-30.0,
        maximum_latitude_deg=30.0,
    )

    assert result.points == ()


def test_polar_reference_case() -> None:
    position = satellite.SatellitePosition.from_geodetic(
        epoch_utc="epoch-1",
        latitude_deg=90.0,
        longitude_deg=0.0,
        altitude_m=1_000.0,
    )
    pole = wgs84.geodetic_to_ecef(wgs84.GeodeticPoint(90.0, 0.0, 0.0))
    target = slant_range.slant_range_m(pole, position)

    result = locus.generate_surface_locus(
        position,
        target,
        tolerance_m=0.01,
        longitude_step_deg=90.0,
        latitude_step_deg=10.0,
        minimum_longitude_deg=-90.0,
        maximum_longitude_deg=90.0,
        minimum_latitude_deg=80.0,
        maximum_latitude_deg=90.0,
    )

    assert result.points
    assert all(point.geodetic.latitude_deg == 90.0 for point in result.points)


def test_invalid_inputs_fail_closed() -> None:
    position = _reference_satellite()

    for value in (0.0, -1.0, math.nan, math.inf):
        with pytest.raises(ValueError):
            locus.generate_surface_locus(position, value)
    with pytest.raises(TypeError, match="satellite"):
        locus.generate_surface_locus(position.ecef, 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="longitude bounds"):
        locus.generate_surface_locus(
            position,
            1.0,
            minimum_longitude_deg=10.0,
            maximum_longitude_deg=-10.0,
        )
    with pytest.raises(ValueError, match="latitude bounds"):
        locus.generate_surface_locus(
            position,
            1.0,
            minimum_latitude_deg=10.0,
            maximum_latitude_deg=-10.0,
        )
    with pytest.raises(ValueError, match="maximum_iterations"):
        locus.generate_surface_locus(position, 1.0, maximum_iterations=0)
