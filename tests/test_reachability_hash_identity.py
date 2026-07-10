"""Tests for exact L1.3 reachability identity hashes."""

from mh370_inverse_inference.aircraft.envelope import (
    ControlBounds,
    ReachabilityRequest,
    evaluate_reachability,
)
from mh370_inverse_inference.aircraft.state import AircraftState


def build_request(*, max_turn_rate_degps: float = 0.0) -> ReachabilityRequest:
    return ReachabilityRequest(
        initial_state=AircraftState(
            timestamp_utc="2014-03-08T18:22:00Z",
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=10000.0,
            true_airspeed_mps=200.0,
            heading_deg=90.0,
            mass_kg=200000.0,
            model_version="aircraft-dynamics-1.0.0",
        ),
        control_bounds=ControlBounds(
            min_climb_rate_mps=0.0,
            max_climb_rate_mps=0.0,
            min_turn_rate_degps=0.0,
            max_turn_rate_degps=max_turn_rate_degps,
            min_true_airspeed_mps=200.0,
            max_true_airspeed_mps=200.0,
            control_step_count=1,
        ),
        dt_seconds=60.0,
        step_count=1,
        model_version="aircraft-dynamics-1.0.0",
    )


def test_control_bound_change_changes_input_hash() -> None:
    baseline = evaluate_reachability(build_request())
    changed = evaluate_reachability(build_request(max_turn_rate_degps=0.5))

    assert baseline.input_hash != changed.input_hash


def test_metadata_matches_emitted_states() -> None:
    summary = evaluate_reachability(build_request())
    states = tuple(record.state for record in summary.reachable_states)

    assert summary.envelope_metadata.min_latitude_deg == min(
        state.latitude_deg for state in states
    )
    assert summary.envelope_metadata.max_longitude_deg == max(
        state.longitude_deg for state in states
    )
    assert summary.envelope_metadata.state_count == len(states)
