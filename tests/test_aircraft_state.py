"""Tests for the bounded L1.1 aircraft-state contract."""

from dataclasses import FrozenInstanceError, replace

import pytest

from mh370_inverse_inference.aircraft.radar import RadarTrackPoint, RadarUncertainty
from mh370_inverse_inference.aircraft.state import (
    AIRCRAFT_STATE_CONTRACT_VERSION,
    AircraftState,
    AircraftStateTransition,
)


def _state(timestamp: str = "2014-03-07T18:22:00Z") -> AircraftState:
    return AircraftState(
        timestamp_utc=timestamp,
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=10_668.0,
        groundspeed_mps=250.0,
        heading_deg=270.0,
        source_id="radar-source-example",
        source_version="v1",
    )


def _radar_point() -> RadarTrackPoint:
    return RadarTrackPoint(
        timestamp_utc="2014-03-07T18:22:00Z",
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=10_668.0,
        groundspeed_mps=250.0,
        heading_deg=270.0,
        source_id="radar-source-example",
        source_version="v1",
        uncertainty=RadarUncertainty(
            position_m=1_000.0,
            speed_mps=10.0,
            heading_deg=5.0,
        ),
    )


def test_valid_state_is_immutable_and_deterministic() -> None:
    state = _state()
    assert state.contract_version == AIRCRAFT_STATE_CONTRACT_VERSION
    assert state.to_payload() == _state().to_payload()
    with pytest.raises(FrozenInstanceError):
        state.heading_deg = 0.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "timestamp",
    (
        "2014-03-07T18:22:00+00:00",
        "2014-03-07 18:22:00Z",
        "not-a-time",
    ),
)
def test_noncanonical_timestamps_fail_closed(timestamp: str) -> None:
    with pytest.raises(ValueError):
        replace(_state(), timestamp_utc=timestamp)


@pytest.mark.parametrize(
    "field,value",
    (
        ("latitude_deg", -90.1),
        ("latitude_deg", 90.1),
        ("longitude_deg", -180.1),
        ("longitude_deg", 180.1),
        ("altitude_m", -1.0),
        ("groundspeed_mps", -1.0),
        ("heading_deg", -0.1),
        ("heading_deg", 360.0),
        ("latitude_deg", float("nan")),
        ("longitude_deg", float("inf")),
        ("altitude_m", float("-inf")),
    ),
)
def test_invalid_numeric_values_fail_closed(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        replace(_state(), **{field: value})


def test_blank_source_identity_and_wrong_contract_fail_closed() -> None:
    with pytest.raises(ValueError):
        replace(_state(), source_id="")
    with pytest.raises(ValueError):
        replace(_state(), source_version="")
    with pytest.raises(ValueError):
        replace(_state(), contract_version="wrong")


def test_radar_initialisation_preserves_exact_values_without_inference() -> None:
    point = _radar_point()
    state = AircraftState.from_radar_track_point(point)
    assert state.to_payload() == {
        "altitude_m": 10_668.0,
        "contract_version": AIRCRAFT_STATE_CONTRACT_VERSION,
        "groundspeed_mps": 250.0,
        "heading_deg": 270.0,
        "latitude_deg": 6.0,
        "longitude_deg": 100.0,
        "source_id": "radar-source-example",
        "source_version": "v1",
        "timestamp_utc": "2014-03-07T18:22:00Z",
    }
    assert "mass_kg" not in state.to_payload()
    assert "true_airspeed_mps" not in state.to_payload()


def test_transition_requires_exact_positive_elapsed_time() -> None:
    previous = _state()
    current = _state("2014-03-07T18:23:00Z")
    transition = AircraftStateTransition(previous, current, 60.0)
    assert transition.to_payload()["elapsed_seconds"] == 60.0

    with pytest.raises(ValueError):
        AircraftStateTransition(previous, current, 0.0)
    with pytest.raises(ValueError):
        AircraftStateTransition(previous, current, -1.0)
    with pytest.raises(ValueError, match="timestamp difference"):
        AircraftStateTransition(previous, current, 59.0)
    with pytest.raises(ValueError, match="later"):
        AircraftStateTransition(current, previous, 60.0)


def test_transition_is_immutable() -> None:
    transition = AircraftStateTransition(
        _state(),
        _state("2014-03-07T18:23:00Z"),
        60.0,
    )
    with pytest.raises(FrozenInstanceError):
        transition.elapsed_seconds = 61.0  # type: ignore[misc]
