"""Tests for canonical aircraft-state serialization."""

from dataclasses import is_dataclass

import pytest

from mh370_inverse_inference.aircraft.serialization import (
    canonical_hash,
    canonical_json,
)
from mh370_inverse_inference.aircraft.state import AircraftState


def sample_state(model_version: str = "L1.1-test") -> AircraftState:
    return AircraftState(
        timestamp_utc="2014-03-08T18:22:00Z",
        latitude_deg=6.5,
        longitude_deg=95.0,
        altitude_m=10668.0,
        true_airspeed_mps=236.0,
        heading_deg=255.0,
        mass_kg=220000.0,
        model_version=model_version,
    )


def test_aircraft_state_is_frozen_dataclass() -> None:
    state = sample_state()

    assert is_dataclass(state)
    assert state.__dataclass_params__.frozen is True


def test_aircraft_state_canonical_json_is_stable() -> None:
    state = sample_state()

    assert canonical_json(state) == canonical_json(state)


def test_aircraft_state_hash_is_stable_for_identical_payloads() -> None:
    first = sample_state()
    second = sample_state()

    assert canonical_hash(first) == canonical_hash(second)


def test_aircraft_state_model_version_changes_hash() -> None:
    first = sample_state(model_version="L1.1-test")
    second = sample_state(model_version="L1.1-test-alt")

    assert canonical_hash(first) != canonical_hash(second)


def test_aircraft_state_rejects_invalid_timestamp() -> None:
    with pytest.raises(ValueError, match="timestamp_utc"):
        AircraftState(
            timestamp_utc="2014-03-08T18:22:00+00:00",
            latitude_deg=6.5,
            longitude_deg=95.0,
            altitude_m=10668.0,
            true_airspeed_mps=236.0,
            heading_deg=255.0,
            mass_kg=220000.0,
            model_version="L1.1-test",
        )
