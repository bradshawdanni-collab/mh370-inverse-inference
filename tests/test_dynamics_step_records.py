"""Tests for canonical dynamics request and step-result records."""

from dataclasses import is_dataclass

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
    DynamicsStepResult,
)
from mh370_inverse_inference.aircraft.serialization import canonical_hash, canonical_json
from mh370_inverse_inference.aircraft.state import AircraftState


def state_at(timestamp_utc: str, latitude_deg: float) -> AircraftState:
    return AircraftState(
        timestamp_utc=timestamp_utc,
        latitude_deg=latitude_deg,
        longitude_deg=95.0,
        altitude_m=10668.0,
        true_airspeed_mps=236.0,
        heading_deg=255.0,
        mass_kg=220000.0,
        model_version="L1.1-test",
    )


def test_dynamics_records_are_frozen_dataclasses() -> None:
    control = DynamicsControlInput()
    request = DynamicsRequest(
        initial_state=state_at("2014-03-08T18:22:00Z", 6.5),
        control_input=control,
        dt_seconds=60.0,
        model_version="L1.1-test",
    )
    result = DynamicsStepResult(
        previous_state=request.initial_state,
        next_state=state_at("2014-03-08T18:23:00Z", 6.45),
        control_input=control,
        dt_seconds=request.dt_seconds,
        model_version=request.model_version,
        metrics={"fuel_mass_kg": 85000.0},
    )

    assert is_dataclass(control)
    assert is_dataclass(request)
    assert is_dataclass(result)
    assert control.__dataclass_params__.frozen is True
    assert request.__dataclass_params__.frozen is True
    assert result.__dataclass_params__.frozen is True


def test_dynamics_request_serialization_and_hash_are_stable() -> None:
    request = DynamicsRequest(
        initial_state=state_at("2014-03-08T18:22:00Z", 6.5),
        control_input=DynamicsControlInput(climb_rate_mps=0.0, turn_rate_degps=0.0),
        dt_seconds=60.0,
        model_version="L1.1-test",
    )

    assert canonical_json(request) == canonical_json(request)
    assert canonical_hash(request) == canonical_hash(request)


def test_dynamics_step_result_hash_changes_with_model_version() -> None:
    previous = state_at("2014-03-08T18:22:00Z", 6.5)
    next_state = state_at("2014-03-08T18:23:00Z", 6.45)
    control = DynamicsControlInput()
    first = DynamicsStepResult(
        previous_state=previous,
        next_state=next_state,
        control_input=control,
        dt_seconds=60.0,
        model_version="L1.1-test",
        metrics={"constraint_violation": 0.0},
    )
    second = DynamicsStepResult(
        previous_state=previous,
        next_state=next_state,
        control_input=control,
        dt_seconds=60.0,
        model_version="L1.1-test-alt",
        metrics={"constraint_violation": 0.0},
    )

    assert canonical_hash(first) != canonical_hash(second)


def test_dynamics_metrics_are_sorted_for_payload_stability() -> None:
    result = DynamicsStepResult(
        previous_state=state_at("2014-03-08T18:22:00Z", 6.5),
        next_state=state_at("2014-03-08T18:23:00Z", 6.45),
        control_input=DynamicsControlInput(),
        dt_seconds=60.0,
        model_version="L1.1-test",
        metrics={"fuel_mass_kg": 85000.0, "constraint_violation": 0.0},
    )

    assert list(result.metrics) == ["constraint_violation", "fuel_mass_kg"]
