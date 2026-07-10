"""Deterministic L1.3 control bounds and reachability summaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
)
from mh370_inverse_inference.aircraft.propagator import propagate
from mh370_inverse_inference.aircraft.state import AircraftState
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L1.3"
OPERATION = "aircraft_reachability_envelope"


def _finite(value: float, name: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    return resolved


def _axis_values(lower: float, upper: float, count: int) -> tuple[float, ...]:
    if count == 1:
        return (lower,)
    step = (upper - lower) / (count - 1)
    return tuple(lower + index * step for index in range(count))


@dataclass(frozen=True, slots=True)
class ControlBounds:
    """Finite deterministic bounds for the L1.3 control grid."""

    min_climb_rate_mps: float
    max_climb_rate_mps: float
    min_turn_rate_degps: float
    max_turn_rate_degps: float
    min_true_airspeed_mps: float
    max_true_airspeed_mps: float
    control_step_count: int

    def __post_init__(self) -> None:
        numeric_fields = (
            "min_climb_rate_mps",
            "max_climb_rate_mps",
            "min_turn_rate_degps",
            "max_turn_rate_degps",
            "min_true_airspeed_mps",
            "max_true_airspeed_mps",
        )
        for name in numeric_fields:
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if self.control_step_count <= 0:
            raise ValueError("control_step_count must be positive")
        if self.min_climb_rate_mps > self.max_climb_rate_mps:
            raise ValueError("climb-rate lower bound exceeds upper bound")
        if self.min_turn_rate_degps > self.max_turn_rate_degps:
            raise ValueError("turn-rate lower bound exceeds upper bound")
        if self.min_true_airspeed_mps > self.max_true_airspeed_mps:
            raise ValueError("airspeed lower bound exceeds upper bound")
        if self.min_true_airspeed_mps < 0.0:
            raise ValueError("minimum true airspeed cannot be negative")

    def controls(self) -> tuple[DynamicsControlInput, ...]:
        """Generate the stable climb, turn, speed control-product ordering."""
        climb_values = _axis_values(
            self.min_climb_rate_mps,
            self.max_climb_rate_mps,
            self.control_step_count,
        )
        turn_values = _axis_values(
            self.min_turn_rate_degps,
            self.max_turn_rate_degps,
            self.control_step_count,
        )
        speed_values = _axis_values(
            self.min_true_airspeed_mps,
            self.max_true_airspeed_mps,
            self.control_step_count,
        )
        return tuple(
            DynamicsControlInput(
                climb_rate_mps=climb_rate,
                turn_rate_degps=turn_rate,
                target_true_airspeed_mps=speed,
            )
            for climb_rate in climb_values
            for turn_rate in turn_values
            for speed in speed_values
        )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical bounds payload."""
        return {
            "control_step_count": self.control_step_count,
            "max_climb_rate_mps": self.max_climb_rate_mps,
            "max_true_airspeed_mps": self.max_true_airspeed_mps,
            "max_turn_rate_degps": self.max_turn_rate_degps,
            "min_climb_rate_mps": self.min_climb_rate_mps,
            "min_true_airspeed_mps": self.min_true_airspeed_mps,
            "min_turn_rate_degps": self.min_turn_rate_degps,
        }


@dataclass(frozen=True, slots=True)
class ReachabilityRequest:
    """Immutable request for a bounded deterministic reachability sweep."""

    initial_state: AircraftState
    control_bounds: ControlBounds
    dt_seconds: float
    step_count: int
    model_version: str
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        dt_seconds = _finite(self.dt_seconds, "dt_seconds")
        if dt_seconds <= 0.0:
            raise ValueError("dt_seconds must be positive")
        if self.step_count <= 0:
            raise ValueError("step_count must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {CONTRACT_VERSION}")
        object.__setattr__(self, "dt_seconds", dt_seconds)

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload."""
        return {
            "contract_version": self.contract_version,
            "control_bounds": self.control_bounds.to_payload(),
            "dt_seconds": self.dt_seconds,
            "initial_state": self.initial_state.to_payload(),
            "model_version": self.model_version,
            "step_count": self.step_count,
        }


@dataclass(frozen=True, slots=True)
class ReachableStateRecord:
    """One immutable reachable-state record with stable lineage indices."""

    state_index: int
    control_index: int
    parent_state_index: int
    step_index: int
    state: AircraftState
    control_input: DynamicsControlInput
    state_hash: str

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical state-record payload."""
        return {
            "control_index": self.control_index,
            "control_input": self.control_input.to_payload(),
            "parent_state_index": self.parent_state_index,
            "state": self.state.to_payload(),
            "state_hash": self.state_hash,
            "state_index": self.state_index,
            "step_index": self.step_index,
        }


@dataclass(frozen=True, slots=True)
class EnvelopeMetadata:
    """Minima, maxima, and counts derived only from emitted states."""

    min_latitude_deg: float
    max_latitude_deg: float
    min_longitude_deg: float
    max_longitude_deg: float
    min_altitude_m: float
    max_altitude_m: float
    min_true_airspeed_mps: float
    max_true_airspeed_mps: float
    min_mass_kg: float
    max_mass_kg: float
    control_count: int
    state_count: int
    constraint_violation_count: int

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical envelope metadata payload."""
        return {
            "constraint_violation_count": self.constraint_violation_count,
            "control_count": self.control_count,
            "max_altitude_m": self.max_altitude_m,
            "max_latitude_deg": self.max_latitude_deg,
            "max_longitude_deg": self.max_longitude_deg,
            "max_mass_kg": self.max_mass_kg,
            "max_true_airspeed_mps": self.max_true_airspeed_mps,
            "min_altitude_m": self.min_altitude_m,
            "min_latitude_deg": self.min_latitude_deg,
            "min_longitude_deg": self.min_longitude_deg,
            "min_mass_kg": self.min_mass_kg,
            "min_true_airspeed_mps": self.min_true_airspeed_mps,
            "state_count": self.state_count,
        }


@dataclass(frozen=True, slots=True)
class ReachabilitySummary:
    """Immutable L1.3 reachability result and exact audit identity."""

    request: ReachabilityRequest
    reachable_states: tuple[ReachableStateRecord, ...]
    envelope_metadata: EnvelopeMetadata
    input_hash: str
    output_hash: str
    op_signature_hash: str
    operation: str = OPERATION

    @property
    def reachable_state_count(self) -> int:
        """Return the number of emitted reachable states."""
        return len(self.reachable_states)

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical reachability summary payload."""
        return {
            "contract_version": self.request.contract_version,
            "control_bounds": self.request.control_bounds.to_payload(),
            "dt_seconds": self.request.dt_seconds,
            "envelope_metadata": self.envelope_metadata.to_payload(),
            "initial_state": self.request.initial_state.to_payload(),
            "input_hash": self.input_hash,
            "model_version": self.request.model_version,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reachable_state_count": self.reachable_state_count,
            "reachable_states": [item.to_payload() for item in self.reachable_states],
            "step_count": self.request.step_count,
        }


def _metadata(
    records: tuple[ReachableStateRecord, ...], control_count: int
) -> EnvelopeMetadata:
    states = tuple(record.state for record in records)
    return EnvelopeMetadata(
        min_latitude_deg=min(state.latitude_deg for state in states),
        max_latitude_deg=max(state.latitude_deg for state in states),
        min_longitude_deg=min(state.longitude_deg for state in states),
        max_longitude_deg=max(state.longitude_deg for state in states),
        min_altitude_m=min(state.altitude_m for state in states),
        max_altitude_m=max(state.altitude_m for state in states),
        min_true_airspeed_mps=min(state.true_airspeed_mps for state in states),
        max_true_airspeed_mps=max(state.true_airspeed_mps for state in states),
        min_mass_kg=min(state.mass_kg for state in states),
        max_mass_kg=max(state.mass_kg for state in states),
        control_count=control_count,
        state_count=len(records),
        constraint_violation_count=0,
    )


def evaluate_reachability(request: ReachabilityRequest) -> ReachabilitySummary:
    """Evaluate a stable exhaustive control sweep using only L1.2 propagation."""
    controls = request.control_bounds.controls()
    frontier: tuple[tuple[int, AircraftState], ...] = ((-1, request.initial_state),)
    records: list[ReachableStateRecord] = []

    for step_index in range(request.step_count):
        next_frontier: list[tuple[int, AircraftState]] = []
        for parent_state_index, state in frontier:
            for control_index, control in enumerate(controls):
                result = propagate(
                    DynamicsRequest(
                        initial_state=state,
                        control_input=control,
                        dt_seconds=request.dt_seconds,
                        model_version=request.model_version,
                    ),
                    stage_index=step_index,
                )
                state_index = len(records)
                record = ReachableStateRecord(
                    state_index=state_index,
                    control_index=control_index,
                    parent_state_index=parent_state_index,
                    step_index=step_index,
                    state=result.next_state,
                    control_input=control,
                    state_hash=sha256_payload(result.next_state.to_payload()),
                )
                records.append(record)
                next_frontier.append((state_index, result.next_state))
        frontier = tuple(next_frontier)

    reachable_states = tuple(records)
    metadata = _metadata(reachable_states, len(controls))
    input_hash = sha256_payload(request.to_payload())
    output_material = {
        "envelope_metadata": metadata.to_payload(),
        "reachable_states": [record.to_payload() for record in reachable_states],
    }
    output_hash = sha256_payload(output_material)
    op_signature_hash = sha256_payload(
        {
            "contract_version": request.contract_version,
            "model_version": request.model_version,
            "operation": OPERATION,
        }
    )
    return ReachabilitySummary(
        request=request,
        reachable_states=reachable_states,
        envelope_metadata=metadata,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
    )
