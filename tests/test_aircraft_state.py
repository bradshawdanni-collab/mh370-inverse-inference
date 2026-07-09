"""Tests for L1 aircraft state normalization and performance bounds."""

import math

import pytest

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.state import AircraftState


def test_aircraft_state_normalization() -> None:
    state = AircraftState(
        timestamp_utc="2014-03-08T18:22:00Z",
        latitude_deg=0.0,
        longitude_deg=math.degrees(math.pi + 0.1),
        altitude_m=10_000.0,
        true_airspeed_mps=240.0,
        heading_deg=450.0,
        mass_kg=200_000.0,
        model_version="L1.1-test",
    )

    assert state.longitude < 0.0
    assert math.isclose(state.heading, 0.5 * math.pi)


def test_invalid_latitude() -> None:
    with pytest.raises(ValueError, match="latitude_deg"):
        AircraftState(
            timestamp_utc="2014-03-08T18:22:00Z",
            latitude_deg=120.0,
            longitude_deg=0.0,
            altitude_m=10_000.0,
            true_airspeed_mps=240.0,
            heading_deg=0.0,
            mass_kg=200_000.0,
            model_version="L1.1-test",
        )


def test_performance_envelope_validation() -> None:
    assert PerformanceEnvelope.validate_state(11_000.0, 245.0, 220_000.0)
    assert not PerformanceEnvelope.validate_state(15_000.0, 245.0, 220_000.0)
    assert not PerformanceEnvelope.validate_state(10_000.0, 245.0, 100_000.0)
