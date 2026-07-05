"""Tests for the L8.2 deterministic drift-step primitive."""

import math

import pytest

from mh370_inverse_inference.drift.step import compute_deterministic_step


def test_zero_velocity_step_preserves_position() -> None:
    result = compute_deterministic_step(
        lat=-31.5,
        lon=95.0,
        u_current=0.0,
        v_current=0.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=0.01,
        dt=3600.0,
    )

    assert result == {
        "lat": -31.5,
        "lon": 95.0,
        "u_effective": 0.0,
        "v_effective": 0.0,
    }


def test_pure_current_northward_displacement() -> None:
    result = compute_deterministic_step(
        lat=0.0,
        lon=90.0,
        u_current=0.0,
        v_current=1.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=0.0,
        dt=3600.0,
    )

    assert result["u_effective"] == 0.0
    assert result["v_effective"] == 1.0
    assert result["lon"] == 90.0
    assert result["lat"] == pytest.approx(0.03237558, abs=1e-8)


def test_current_and_windage_combine_linearly() -> None:
    result = compute_deterministic_step(
        lat=-30.0,
        lon=100.0,
        u_current=0.5,
        v_current=0.0,
        u_wind=10.0,
        v_wind=0.0,
        windage=0.02,
        dt=1800.0,
    )

    assert result["u_effective"] == pytest.approx(0.7)
    assert result["v_effective"] == 0.0
    assert result["lat"] == -30.0
    assert result["lon"] > 100.0


def test_longitude_wraps_into_canonical_range() -> None:
    result = compute_deterministic_step(
        lat=0.0,
        lon=179.99,
        u_current=10.0,
        v_current=0.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=0.0,
        dt=3600.0,
    )

    assert -180.0 <= result["lon"] < 180.0
    assert result["lon"] < 0.0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"lat": math.nan}, "finite"),
        ({"lat": 91.0}, "latitude"),
        ({"windage": -0.01}, "windage"),
        ({"dt": -1.0}, "dt"),
        ({"lat": 90.0}, "poles"),
    ],
)
def test_invalid_inputs_fail_closed(
    overrides: dict[str, float], message: str
) -> None:
    arguments = {
        "lat": 0.0,
        "lon": 0.0,
        "u_current": 1.0,
        "v_current": 0.0,
        "u_wind": 0.0,
        "v_wind": 0.0,
        "windage": 0.0,
        "dt": 1.0,
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        compute_deterministic_step(**arguments)


def test_zero_duration_at_pole_is_well_defined() -> None:
    result = compute_deterministic_step(
        lat=90.0,
        lon=45.0,
        u_current=1.0,
        v_current=1.0,
        u_wind=2.0,
        v_wind=2.0,
        windage=0.1,
        dt=0.0,
    )

    assert result["lat"] == 90.0
    assert result["lon"] == 45.0
