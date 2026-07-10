"""Immutable dynamics request and step-result records."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from mh370_inverse_inference.aircraft.state import AircraftState

CONTRACT_VERSION = "L1.2"
OPERATION = "aircraft_dynamics_step"


def _finite(value: float, name: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    return resolved


@dataclass(frozen=True, slots=True)
class DynamicsControlInput:
    """Control inputs for one deterministic dynamics step."""

    climb_rate_mps: float = 0.0
    turn_rate_degps: float = 0.0
    target_true_airspeed_mps: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "climb_rate_mps",
            _finite(self.climb_rate_mps, "climb_rate_mps"),
        )
        object.__setattr__(
            self,
            "turn_rate_degps",
            _finite(self.turn_rate_degps, "turn_rate_degps"),
        )
        if self.target_true_airspeed_mps is not None:
            speed = _finite(
                self.target_true_airspeed_mps,
                "target_true_airspeed_mps",
            )
            if speed < 0.0:
                raise ValueError("target_true_airspeed_mps cannot be negative")
            object.__setattr__(self, "target_true_airspeed_mps", speed)

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible control payload."""
        return {
            "climb_rate_mps": self.climb_rate_mps,
            "target_true_airspeed_mps": self.target_true_airspeed_mps,
            "turn_rate_degps": self.turn_rate_degps,
        }


@dataclass(frozen=True, slots=True)
class DynamicsRequest:
    """Complete deterministic input contract for one dynamics step."""

    initial_state: AircraftState
    control_input: DynamicsControlInput
    dt_seconds: float
    model_version: str

    def __post_init__(self) -> None:
        dt_seconds = _finite(self.dt_seconds, "dt_seconds")
        if dt_seconds <= 0.0:
            raise ValueError("dt_seconds must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")
        object.__setattr__(self, "dt_seconds", dt_seconds)

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible request payload."""
        return {
            "control_input": self.control_input.to_payload(),
            "dt_seconds": self.dt_seconds,
            "initial_state": self.initial_state.to_payload(),
            "model_version": self.model_version,
        }


@dataclass(frozen=True, slots=True)
class DynamicsStepResult:
    """Immutable, audit-ready result of one deterministic state transition."""

    previous_state: AircraftState
    next_state: AircraftState
    control_input: DynamicsControlInput
    dt_seconds: float
    model_version: str
    stage_index: int
    input_hash: str
    output_hash: str
    op_signature_hash: str
    contract_version: str = CONTRACT_VERSION
    operation: str = OPERATION
    metrics: Mapping[str, float | int | str | bool | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dt_seconds = _finite(self.dt_seconds, "dt_seconds")
        if dt_seconds <= 0.0:
            raise ValueError("dt_seconds must be positive")
        if self.stage_index < 0:
            raise ValueError("stage_index cannot be negative")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {CONTRACT_VERSION}")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        for name in ("input_hash", "output_hash", "op_signature_hash"):
            value = getattr(self, name)
            invalid_character = any(char not in "0123456789abcdef" for char in value)
            if len(value) != 64 or invalid_character:
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        ordered_metrics = dict(sorted(self.metrics.items()))
        for key, value in ordered_metrics.items():
            if isinstance(value, float):
                _finite(value, f"metrics.{key}")
        object.__setattr__(self, "dt_seconds", dt_seconds)
        object.__setattr__(self, "metrics", MappingProxyType(ordered_metrics))

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical auditable step-result payload."""
        return {
            "contract_version": self.contract_version,
            "control_input": self.control_input.to_payload(),
            "dt_seconds": self.dt_seconds,
            "input_hash": self.input_hash,
            "metrics": dict(self.metrics),
            "model_version": self.model_version,
            "next_state": self.next_state.to_payload(),
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "previous_state": self.previous_state.to_payload(),
            "stage_index": self.stage_index,
        }
