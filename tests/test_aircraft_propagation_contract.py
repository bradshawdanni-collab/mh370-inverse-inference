"""Tests for deterministic propagation against an admitted envelope."""

# fmt: off

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.aircraft.envelope_contract import (
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.aircraft.propagation_contract import (
    PropagationCommand,
    propagate_state,
)
from mh370_inverse_inference.aircraft.state_contract import AircraftStateInput
from mh370_inverse_inference.provenance import ArtifactAdmissionState


def _state() -> AircraftStateInput:
    return AircraftStateInput(
        timestamp_utc="2014-03-07T18:22:00Z",
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=10_000.0,
        groundspeed_mps=240.0,
        heading_deg=270.0,
        source_id="radar-source",
        source_version="v1",
    )


def _envelope(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> AircraftOperatingEnvelope:
    return AircraftOperatingEnvelope(
        minimum_speed_mps=180.0,
        maximum_speed_mps=280.0,
        minimum_altitude_m=0.0,
        maximum_altitude_m=13_000.0,
        maximum_climb_rate_mps=10.0,
        maximum_descent_rate_mps=12.0,
        maximum_turn_rate_deg_s=3.0,
        source_id="performance-source",
        source_version="v2",
        model_version="B777-envelope-v1",
        admission_state=admission_state,
    )


def test_propagation_is_deterministic_and_preserves_identity() -> None:
    state = _state()
    command = PropagationCommand(
        elapsed_seconds=60.0,
        target_speed_mps=250.0,
        target_altitude_m=10_300.0,
        target_heading_deg=280.0,
    )
    result = propagate_state(state, command, _envelope())

    assert result.next_state.timestamp_utc == "2014-03-07T18:23:00Z"
    assert result.next_state.latitude_deg == state.latitude_deg
    assert result.next_state.longitude_deg == state.longitude_deg
    assert result.next_state.source_id == state.source_id
    assert result.next_state.source_version == state.source_version
    assert result.transition.previous == state
    assert result.transition.current == result.next_state
    assert result.transition.elapsed_seconds == 60.0
    assert result.envelope_source_id == "performance-source"
    assert result.envelope_source_version == "v2"
    assert result.envelope_model_version == "B777-envelope-v1"
    assert result.to_payload() == propagate_state(
        state,
        command,
        _envelope(),
    ).to_payload()


def test_propagation_requires_admitted_envelope() -> None:
    command = PropagationCommand(60.0, 240.0, 10_000.0, 270.0)
    with pytest.raises(ValueError, match="ADMITTED"):
        propagate_state(
            _state(),
            command,
            _envelope(ArtifactAdmissionState.PROPOSED),
        )


@pytest.mark.parametrize("target_speed", (179.9, 280.1))
def test_speed_outside_envelope_fails_closed(target_speed: float) -> None:
    command = PropagationCommand(60.0, target_speed, 10_000.0, 270.0)
    with pytest.raises(ValueError, match="speed"):
        propagate_state(_state(), command, _envelope())


@pytest.mark.parametrize("target_altitude", (-1.0, 13_000.1))
def test_altitude_outside_envelope_fails_closed(target_altitude: float) -> None:
    if target_altitude < 0.0:
        with pytest.raises(ValueError, match="target_altitude_m"):
            PropagationCommand(60.0, 240.0, target_altitude, 270.0)
        return
    command = PropagationCommand(60.0, 240.0, target_altitude, 270.0)
    with pytest.raises(ValueError, match="altitude"):
        propagate_state(_state(), command, _envelope())


def test_climb_descent_and_turn_limits_fail_closed() -> None:
    with pytest.raises(ValueError, match="climb"):
        propagate_state(
            _state(),
            PropagationCommand(10.0, 240.0, 10_101.0, 270.0),
            _envelope(),
        )
    with pytest.raises(ValueError, match="descent"):
        propagate_state(
            _state(),
            PropagationCommand(10.0, 240.0, 9_879.0, 270.0),
            _envelope(),
        )
    with pytest.raises(ValueError, match="turn"):
        propagate_state(
            _state(),
            PropagationCommand(10.0, 240.0, 10_000.0, 301.0),
            _envelope(),
        )


def test_shortest_heading_delta_is_used() -> None:
    state = AircraftStateInput(
        timestamp_utc="2014-03-07T18:22:00Z",
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=10_000.0,
        groundspeed_mps=240.0,
        heading_deg=359.0,
        source_id="radar-source",
        source_version="v1",
    )
    result = propagate_state(
        state,
        PropagationCommand(1.0, 240.0, 10_000.0, 1.0),
        _envelope(),
    )
    assert result.next_state.heading_deg == 1.0


def test_command_and_result_are_immutable() -> None:
    command = PropagationCommand(60.0, 240.0, 10_000.0, 270.0)
    result = propagate_state(_state(), command, _envelope())
    with pytest.raises(FrozenInstanceError):
        command.elapsed_seconds = 1.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.envelope_model_version = "changed"  # type: ignore[misc]
