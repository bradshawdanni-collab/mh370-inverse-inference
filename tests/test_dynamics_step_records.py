"""Tests for canonical dynamics request and step-result records."""

from dataclasses import is_dataclass

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
)
from mh370_inverse_inference.aircraft.propagator import propagate
from mh370_inverse_inference.aircraft.serialization import (
    canonical_hash,
    canonical_json,
)
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
        model_version="aircraft-dynamics-1.0.0",
    )


def request_at(timestamp_utc: str = "2014-03-08T18:22:00Z") -> DynamicsRequest:
    return DynamicsRequest(
        initial_state=state_at(timestamp_utc, 6.5),
        control_input=DynamicsControlInput(),
        dt_seconds=60.0,
        model_version="aircraft-dynamics-1.0.0",
    )


def test_dynamics_records_are_frozen_dataclasses() -> None:
    request = request_at()
    result = propagate(request)

    assert is_dataclass(request.control_input)
    assert is_dataclass(request)
    assert is_dataclass(result)
    assert request.control_input.__dataclass_params__.frozen is True
    assert request.__dataclass_params__.frozen is True
    assert result.__dataclass_params__.frozen is True


def test_dynamics_request_serialization_and_hash_are_stable() -> None:
    request = request_at()

    assert canonical_json(request) == canonical_json(request)
    assert canonical_hash(request) == canonical_hash(request)


def test_dynamics_step_result_hash_changes_with_model_version() -> None:
    first = propagate(request_at())
    altered = DynamicsRequest(
        initial_state=request_at().initial_state,
        control_input=DynamicsControlInput(),
        dt_seconds=60.0,
        model_version="aircraft-dynamics-1.0.1",
    )
    second = propagate(altered)

    assert first.input_hash != second.input_hash
    assert first.op_signature_hash != second.op_signature_hash


def test_dynamics_metrics_are_sorted_for_payload_stability() -> None:
    result = propagate(request_at())

    assert list(result.metrics) == [
        "constraint_violation",
        "fuel_consumed_kg",
    ]
