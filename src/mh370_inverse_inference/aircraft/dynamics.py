"""Immutable dynamics request and step-result records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mh370_inverse_inference.aircraft.state import AircraftState


@dataclass(frozen=True, slots=True)
class DynamicsControlInput:
    """Control inputs for one future deterministic dynamics step."""

    climb_rate_mps: float = 0.0
    turn_rate_degps: float = 0.0
    target_true_airspeed_mps: float | None = None

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
        if self.dt_seconds <= 0.0:
            raise ValueError("dt_seconds must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")

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
    """Canonical record of one deterministic state transition.

    This object records a transition contract only. It does not perform tracing
    and does not imply that a full aircraft propagator exists yet.
    """

    previous_state: AircraftState
    next_state: AircraftState
    control_input: DynamicsControlInput
    dt_seconds: float
    model_version: str
    metrics: dict[str, float | int | str | bool | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.dt_seconds <= 0.0:
            raise ValueError("dt_seconds must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")
        object.__setattr__(self, "metrics", dict(sorted(self.metrics.items())))

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible step-result payload."""
        return {
            "control_input": self.control_input.to_payload(),
            "dt_seconds": self.dt_seconds,
            "metrics": self.metrics,
            "model_version": self.model_version,
            "next_state": self.next_state.to_payload(),
            "previous_state": self.previous_state.to_payload(),
        }
