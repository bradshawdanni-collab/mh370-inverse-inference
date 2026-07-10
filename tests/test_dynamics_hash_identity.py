"""Tests for exact L1.2 dynamics identity hashes."""

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
)
from mh370_inverse_inference.aircraft.propagator import propagate
from mh370_inverse_inference.aircraft.serialization import canonical_json
from mh370_inverse_inference.aircraft.state import AircraftState


def make_request(
    *,
    dt_seconds: float = 60.0,
    model_version: str = "aircraft-dynamics-1.0.0",
    climb_rate_mps: float = 0.0,
) -> DynamicsRequest:
    return DynamicsRequest(
        initial_state=AircraftState(
            timestamp_utc="2014-03-08T18:22:00Z",
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=10000.0,
            true_airspeed_mps=200.0,
            heading_deg=90.0,
            mass_kg=200000.0,
            model_version=model_version,
        ),
        control_input=DynamicsControlInput(climb_rate_mps=climb_rate_mps),
        dt_seconds=dt_seconds,
        model_version=model_version,
    )


def test_identical_requests_produce_exact_identity() -> None:
    first = propagate(make_request())
    second = propagate(make_request())

    assert canonical_json(first) == canonical_json(second)
    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.op_signature_hash == second.op_signature_hash


def test_model_version_changes_identity_hashes() -> None:
    first = propagate(make_request())
    second = propagate(make_request(model_version="aircraft-dynamics-1.0.1"))

    assert first.input_hash != second.input_hash
    assert first.op_signature_hash != second.op_signature_hash


def test_state_control_or_timestep_changes_input_hash() -> None:
    baseline = propagate(make_request())
    changed_control = propagate(make_request(climb_rate_mps=1.0))
    changed_timestep = propagate(make_request(dt_seconds=30.0))

    assert baseline.input_hash != changed_control.input_hash
    assert baseline.input_hash != changed_timestep.input_hash
