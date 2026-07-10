"""Tests for the pure fixed-step L1.2 propagator."""

import math

import pytest

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
)
from mh370_inverse_inference.aircraft.propagator import propagate
from mh370_inverse_inference.aircraft.state import AircraftState

ABS_TOL = 1e-12
REL_TOL = 1e-12


def request(
    *,
    climb_rate_mps: float = 0.0,
    turn_rate_degps: float = 0.0,
    model_version: str = "aircraft-dynamics-1.0.0",
) -> DynamicsRequest:
    state = AircraftState(
        timestamp_utc="2014-03-08T18:22:00Z",
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_m=10000.0,
        true_airspeed_mps=200.0,
        heading_deg=90.0,
        mass_kg=200000.0,
        model_version=model_version,
    )
    return DynamicsRequest(
        initial_state=state,
        control_input=DynamicsControlInput(
            climb_rate_mps=climb_rate_mps,
            turn_rate_degps=turn_rate_degps,
        ),
        dt_seconds=60.0,
        model_version=model_version,
    )


def test_repeated_execution_is_identical() -> None:
    first = propagate(request())
    second = propagate(request())

    assert first == second
    assert first.to_payload() == second.to_payload()


def test_inputs_remain_unchanged() -> None:
    dynamics_request = request(climb_rate_mps=5.0)
    before = dynamics_request.to_payload()

    propagate(dynamics_request)

    assert dynamics_request.to_payload() == before


def test_climb_and_turn_are_applied_once() -> None:
    result = propagate(request(climb_rate_mps=5.0, turn_rate_degps=0.5))

    assert result.next_state.altitude_m == pytest.approx(
        10300.0,
        abs=ABS_TOL,
        rel=REL_TOL,
    )
    assert result.next_state.heading_deg == pytest.approx(
        120.0,
        abs=ABS_TOL,
        rel=REL_TOL,
    )


def test_non_finite_control_fails_closed() -> None:
    with pytest.raises(ValueError, match="finite"):
        DynamicsControlInput(climb_rate_mps=math.inf)


def test_non_positive_timestep_fails_closed() -> None:
    base = request()
    with pytest.raises(ValueError, match="positive"):
        DynamicsRequest(
            initial_state=base.initial_state,
            control_input=base.control_input,
            dt_seconds=0.0,
            model_version=base.model_version,
        )
