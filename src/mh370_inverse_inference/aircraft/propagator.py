"""Pure fixed-step aircraft propagator for L1.2."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from mh370_inverse_inference.aircraft.dynamics import (
    CONTRACT_VERSION,
    OPERATION,
    DynamicsRequest,
    DynamicsStepResult,
)
from mh370_inverse_inference.aircraft.serialization import (
    dynamics_input_hash,
    dynamics_operation_hash,
    dynamics_output_hash,
)
from mh370_inverse_inference.aircraft.state import AircraftState

EARTH_RADIUS_M = 6_371_000.0


def _advance_timestamp(timestamp_utc: str, dt_seconds: float) -> str:
    parsed = datetime.fromisoformat(timestamp_utc.removesuffix("Z") + "+00:00")
    advanced = parsed + timedelta(seconds=dt_seconds)
    return advanced.isoformat().replace("+00:00", "Z")


def propagate(request: DynamicsRequest, *, stage_index: int = 0) -> DynamicsStepResult:
    """Propagate one deterministic step in a fixed documented operation order."""
    state = request.initial_state
    control = request.control_input
    dt_seconds = request.dt_seconds

    speed_mps = (
        state.true_airspeed_mps
        if control.target_true_airspeed_mps is None
        else control.target_true_airspeed_mps
    )
    altitude_m = max(0.0, state.altitude_m + control.climb_rate_mps * dt_seconds)
    heading_deg = (state.heading_deg + control.turn_rate_degps * dt_seconds) % 360.0

    angular_distance = speed_mps * dt_seconds / EARTH_RADIUS_M
    latitude_1 = math.radians(state.latitude_deg)
    longitude_1 = math.radians(state.longitude_deg)
    heading = math.radians(heading_deg)

    latitude_2 = math.asin(
        math.sin(latitude_1) * math.cos(angular_distance)
        + math.cos(latitude_1) * math.sin(angular_distance) * math.cos(heading)
    )
    longitude_2 = longitude_1 + math.atan2(
        math.sin(heading) * math.sin(angular_distance) * math.cos(latitude_1),
        math.cos(angular_distance) - math.sin(latitude_1) * math.sin(latitude_2),
    )

    next_state = AircraftState(
        timestamp_utc=_advance_timestamp(state.timestamp_utc, dt_seconds),
        latitude_deg=math.degrees(latitude_2),
        longitude_deg=math.degrees(longitude_2),
        altitude_m=altitude_m,
        true_airspeed_mps=speed_mps,
        heading_deg=heading_deg,
        mass_kg=state.mass_kg,
        model_version=request.model_version,
    )
    metrics = {
        "constraint_violation": 0.0,
        "fuel_consumed_kg": 0.0,
    }
    input_hash = dynamics_input_hash(
        previous_state=state.to_payload(),
        control_input=control.to_payload(),
        dt_seconds=dt_seconds,
        model_version=request.model_version,
    )
    output_hash = dynamics_output_hash(
        next_state=next_state.to_payload(),
        metrics=metrics,
    )
    op_signature_hash = dynamics_operation_hash(
        operation=OPERATION,
        contract_version=CONTRACT_VERSION,
        model_version=request.model_version,
    )

    return DynamicsStepResult(
        previous_state=state,
        next_state=next_state,
        control_input=control,
        dt_seconds=dt_seconds,
        model_version=request.model_version,
        stage_index=stage_index,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        metrics=metrics,
    )
