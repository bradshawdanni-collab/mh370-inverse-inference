"""Tests for deterministic L1.3 reachability integration."""

from mh370_inverse_inference.aircraft.envelope import (
    ControlBounds,
    ReachabilityRequest,
    evaluate_reachability,
)
from mh370_inverse_inference.aircraft.state import AircraftState


def request(step_count: int = 1) -> ReachabilityRequest:
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
            max_turn_rate_degps=0.0,
            min_true_airspeed_mps=200.0,
            max_true_airspeed_mps=200.0,
            control_step_count=1,
        ),
        dt_seconds=60.0,
        step_count=step_count,
        model_version="aircraft-dynamics-1.0.0",
    )


def test_single_control_single_step_emits_one_state() -> None:
    summary = evaluate_reachability(request())

    assert summary.reachable_state_count == 1
    assert summary.reachable_states[0].state_index == 0
    assert summary.reachable_states[0].parent_state_index == -1
    assert summary.envelope_metadata.state_count == 1
    assert summary.envelope_metadata.control_count == 1


def test_two_steps_preserve_parent_lineage() -> None:
    summary = evaluate_reachability(request(step_count=2))

    assert summary.reachable_state_count == 2
    assert summary.reachable_states[0].parent_state_index == -1
    assert summary.reachable_states[1].parent_state_index == 0
    assert summary.reachable_states[1].step_index == 1


def test_replay_preserves_order_and_hashes() -> None:
    first = evaluate_reachability(request(step_count=2))
    second = evaluate_reachability(request(step_count=2))

    assert first.to_payload() == second.to_payload()
    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.op_signature_hash == second.op_signature_hash
