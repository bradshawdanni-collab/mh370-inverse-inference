"""Tests for deterministic reachability against an admitted envelope."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.aircraft.envelope_contract import (
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.aircraft.reachability_contract import (
    ReachabilityResult,
    evaluate_reachability,
)
from mh370_inverse_inference.aircraft.state_contract import AircraftStateInput
from mh370_inverse_inference.provenance import ArtifactAdmissionState


def _state(
    *,
    timestamp_utc: str,
    altitude_m: float = 10_000.0,
    groundspeed_mps: float = 240.0,
    heading_deg: float = 270.0,
    source_id: str = "radar-source",
    source_version: str = "v1",
) -> AircraftStateInput:
    return AircraftStateInput(
        timestamp_utc=timestamp_utc,
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=altitude_m,
        groundspeed_mps=groundspeed_mps,
        heading_deg=heading_deg,
        source_id=source_id,
        source_version=source_version,
    )


def _envelope(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
    minimum_altitude_m: float = 0.0,
) -> AircraftOperatingEnvelope:
    return AircraftOperatingEnvelope(
        minimum_speed_mps=180.0,
        maximum_speed_mps=280.0,
        minimum_altitude_m=minimum_altitude_m,
        maximum_altitude_m=13_000.0,
        maximum_climb_rate_mps=10.0,
        maximum_descent_rate_mps=12.0,
        maximum_turn_rate_deg_s=3.0,
        source_id="performance-source",
        source_version="v2",
        model_version="B777-envelope-v1",
        admission_state=admission_state,
    )


def test_admissible_transition_returns_empty_failures() -> None:
    result = evaluate_reachability(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(
            timestamp_utc="2014-03-07T18:23:00Z",
            altitude_m=10_300.0,
            groundspeed_mps=250.0,
            heading_deg=280.0,
            source_id="radar-source-2",
            source_version="v2",
        ),
        _envelope(),
    )

    assert result.admissible is True
    assert result.failed_constraints == ()
    assert result.elapsed_seconds == 60.0
    assert result.start_source_id == "radar-source"
    assert result.end_source_id == "radar-source-2"
    assert result.envelope_source_id == "performance-source"
    assert result.envelope_source_version == "v2"
    assert result.envelope_model_version == "B777-envelope-v1"


def test_non_admitted_envelope_fails_closed() -> None:
    with pytest.raises(ValueError, match="ADMITTED"):
        evaluate_reachability(
            _state(timestamp_utc="2014-03-07T18:22:00Z"),
            _state(timestamp_utc="2014-03-07T18:23:00Z"),
            _envelope(ArtifactAdmissionState.PROPOSED),
        )


def test_non_positive_elapsed_time_fails_closed() -> None:
    with pytest.raises(ValueError, match="later"):
        evaluate_reachability(
            _state(timestamp_utc="2014-03-07T18:22:00Z"),
            _state(timestamp_utc="2014-03-07T18:22:00Z"),
            _envelope(),
        )


def test_explicit_failed_constraints_are_deterministic() -> None:
    result = evaluate_reachability(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(
            timestamp_utc="2014-03-07T18:22:10Z",
            altitude_m=10_101.0,
            groundspeed_mps=281.0,
            heading_deg=301.0,
        ),
        _envelope(),
    )

    assert result.admissible is False
    assert result.failed_constraints == (
        "END_SPEED_OUTSIDE_ENVELOPE",
        "CLIMB_RATE_EXCEEDED",
        "TURN_RATE_EXCEEDED",
    )


def test_descent_and_end_altitude_failures_are_reported() -> None:
    result = evaluate_reachability(
        _state(timestamp_utc="2014-03-07T18:22:00Z", altitude_m=1_000.0),
        _state(
            timestamp_utc="2014-03-07T18:22:10Z",
            altitude_m=400.0,
        ),
        _envelope(minimum_altitude_m=500.0),
    )

    assert result.failed_constraints == (
        "END_ALTITUDE_OUTSIDE_ENVELOPE",
        "DESCENT_RATE_EXCEEDED",
    )


def test_shortest_heading_delta_is_used() -> None:
    result = evaluate_reachability(
        _state(
            timestamp_utc="2014-03-07T18:22:00Z",
            heading_deg=359.0,
        ),
        _state(
            timestamp_utc="2014-03-07T18:22:01Z",
            heading_deg=1.0,
        ),
        _envelope(),
    )

    assert result.admissible is True


def test_result_payload_is_deterministic() -> None:
    start = _state(timestamp_utc="2014-03-07T18:22:00Z")
    end = _state(timestamp_utc="2014-03-07T18:23:00Z")
    first = evaluate_reachability(start, end, _envelope())
    second = evaluate_reachability(start, end, _envelope())

    assert first.to_payload() == second.to_payload()


def test_result_is_immutable() -> None:
    result = evaluate_reachability(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(timestamp_utc="2014-03-07T18:23:00Z"),
        _envelope(),
    )

    with pytest.raises(FrozenInstanceError):
        result.admissible = False  # type: ignore[misc]


def test_result_rejects_inconsistent_manual_construction() -> None:
    with pytest.raises(ValueError, match="cannot contain"):
        ReachabilityResult(
            admissible=True,
            failed_constraints=("TURN_RATE_EXCEEDED",),
            elapsed_seconds=60.0,
            start_source_id="start",
            start_source_version="v1",
            end_source_id="end",
            end_source_version="v1",
            envelope_source_id="envelope",
            envelope_source_version="v1",
            envelope_model_version="model-v1",
        )
