"""Tests for L1 aircraft state normalization and performance bounds."""

import math

import pytest

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.state import AircraftState


def test_aircraft_state_normalization() -> None:
    state = AircraftState(
        latitude=0.0,
        longitude=math.pi + 0.1,
        altitude=10_000.0,
        speed_tas=240.0,
        heading=2.5 * math.pi,
        mass=200_000.0,
    )

    assert state.longitude < 0.0
    assert math.isclose(state.heading, 0.5 * math.pi)


def test_invalid_latitude() -> None:
    with pytest.raises(ValueError, match="Latitude"):
        AircraftState(
            latitude=2.0,
            longitude=0.0,
            altitude=10_000.0,
            speed_tas=240.0,
            heading=0.0,
            mass=200_000.0,
        )


def test_performance_envelope_validation() -> None:
    assert PerformanceEnvelope.validate_state(11_000.0, 245.0, 220_000.0)
    assert not PerformanceEnvelope.validate_state(15_000.0, 245.0, 220_000.0)
    assert not PerformanceEnvelope.validate_state(10_000.0, 245.0, 100_000.0)
