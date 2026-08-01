"""Deterministic propagation contract against an admitted operating envelope."""

# fmt: off

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from mh370_inverse_inference.aircraft.envelope_contract import (
    AIRCRAFT_ENVELOPE_CONTRACT_VERSION,
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.aircraft.state_contract import (
    AIRCRAFT_STATE_CONTRACT_VERSION,
    AircraftStateInput,
    AircraftStateTransition,
)
from mh370_inverse_inference.provenance import ArtifactAdmissionState

AIRCRAFT_PROPAGATION_CONTRACT_VERSION = "AIRCRAFT-PROPAGATION-1"


def _finite(value: float, name: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be numeric")
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    return resolved


def _parse_timestamp(value: str) -> datetime:
    if type(value) is not str:
        raise TypeError("timestamp_utc must be a string")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")
    return parsed


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _wrapped_heading(value: float) -> float:
    return value % 360.0


@dataclass(frozen=True, slots=True)
class PropagationCommand:
    """Explicit kinematic command without fuel or trajectory semantics."""

    elapsed_seconds: float
    target_speed_mps: float
    target_altitude_m: float
    target_heading_deg: float
    contract_version: str = AIRCRAFT_PROPAGATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        elapsed = _finite(self.elapsed_seconds, "elapsed_seconds")
        speed = _finite(self.target_speed_mps, "target_speed_mps")
        altitude = _finite(self.target_altitude_m, "target_altitude_m")
        heading = _finite(self.target_heading_deg, "target_heading_deg")
        if elapsed <= 0.0:
            raise ValueError("elapsed_seconds must be positive")
        if speed < 0.0:
            raise ValueError("target_speed_mps cannot be negative")
        if altitude < 0.0:
            raise ValueError("target_altitude_m cannot be negative")
        if not 0.0 <= heading < 360.0:
            raise ValueError("target_heading_deg must be within [0, 360)")
        if self.contract_version != AIRCRAFT_PROPAGATION_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be AIRCRAFT-PROPAGATION-1"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "elapsed_seconds": float(self.elapsed_seconds),
            "target_altitude_m": float(self.target_altitude_m),
            "target_heading_deg": float(self.target_heading_deg),
            "target_speed_mps": float(self.target_speed_mps),
        }


@dataclass(frozen=True, slots=True)
class PropagationResult:
    """Deterministic next state and descriptive transition."""

    next_state: AircraftStateInput
    transition: AircraftStateTransition
    envelope_source_id: str
    envelope_source_version: str
    envelope_model_version: str
    contract_version: str = AIRCRAFT_PROPAGATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.contract_version != AIRCRAFT_PROPAGATION_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be AIRCRAFT-PROPAGATION-1"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "envelope_model_version": self.envelope_model_version,
            "envelope_source_id": self.envelope_source_id,
            "envelope_source_version": self.envelope_source_version,
            "next_state": self.next_state.to_payload(),
            "transition": self.transition.to_payload(),
        }


def propagate_state(
    state: AircraftStateInput,
    command: PropagationCommand,
    envelope: AircraftOperatingEnvelope,
) -> PropagationResult:
    """Apply one deterministic kinematic command within an admitted envelope."""
    if type(state) is not AircraftStateInput:
        raise TypeError("state must be AircraftStateInput")
    if type(command) is not PropagationCommand:
        raise TypeError("command must be PropagationCommand")
    if type(envelope) is not AircraftOperatingEnvelope:
        raise TypeError("envelope must be AircraftOperatingEnvelope")
    if state.contract_version != AIRCRAFT_STATE_CONTRACT_VERSION:
        raise ValueError("state contract version is not supported")
    if envelope.contract_version != AIRCRAFT_ENVELOPE_CONTRACT_VERSION:
        raise ValueError("envelope contract version is not supported")
    if envelope.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("operating envelope must be ADMITTED")

    elapsed = float(command.elapsed_seconds)
    if not (
        envelope.minimum_speed_mps
        <= command.target_speed_mps
        <= envelope.maximum_speed_mps
    ):
        raise ValueError("target speed is outside the admitted envelope")
    if not (
        envelope.minimum_altitude_m
        <= command.target_altitude_m
        <= envelope.maximum_altitude_m
    ):
        raise ValueError("target altitude is outside the admitted envelope")

    altitude_delta = command.target_altitude_m - state.altitude_m
    if altitude_delta > envelope.maximum_climb_rate_mps * elapsed:
        raise ValueError("commanded climb exceeds the admitted envelope")
    if -altitude_delta > envelope.maximum_descent_rate_mps * elapsed:
        raise ValueError("commanded descent exceeds the admitted envelope")

    raw_heading_delta = command.target_heading_deg - state.heading_deg
    heading_delta = (raw_heading_delta + 180.0) % 360.0 - 180.0
    if abs(heading_delta) > envelope.maximum_turn_rate_deg_s * elapsed:
        raise ValueError("commanded turn exceeds the admitted envelope")

    next_time = _parse_timestamp(state.timestamp_utc) + timedelta(seconds=elapsed)
    next_state = AircraftStateInput(
        timestamp_utc=_format_timestamp(next_time),
        latitude_deg=state.latitude_deg,
        longitude_deg=state.longitude_deg,
        altitude_m=command.target_altitude_m,
        groundspeed_mps=command.target_speed_mps,
        heading_deg=_wrapped_heading(command.target_heading_deg),
        source_id=state.source_id,
        source_version=state.source_version,
    )
    transition = AircraftStateTransition(
        previous=state,
        current=next_state,
        elapsed_seconds=elapsed,
    )
    return PropagationResult(
        next_state=next_state,
        transition=transition,
        envelope_source_id=envelope.source_id,
        envelope_source_version=envelope.source_version,
        envelope_model_version=envelope.model_version,
    )
