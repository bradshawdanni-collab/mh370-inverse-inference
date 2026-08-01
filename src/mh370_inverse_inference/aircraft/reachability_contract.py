"""Deterministic reachability contract against an admitted envelope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mh370_inverse_inference.aircraft.envelope_contract import (
    AIRCRAFT_ENVELOPE_CONTRACT_VERSION,
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.aircraft.state_contract import (
    AIRCRAFT_STATE_CONTRACT_VERSION,
    AircraftStateInput,
)
from mh370_inverse_inference.provenance import ArtifactAdmissionState

AIRCRAFT_REACHABILITY_CONTRACT_VERSION = "AIRCRAFT-REACHABILITY-1"


def _parse_timestamp(value: str) -> datetime:
    if type(value) is not str:
        raise TypeError("timestamp_utc must be a string")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")
    return parsed


def _shortest_heading_delta(start_deg: float, end_deg: float) -> float:
    raw_delta = end_deg - start_deg
    return (raw_delta + 180.0) % 360.0 - 180.0


@dataclass(frozen=True, slots=True)
class ReachabilityResult:
    """Deterministic admissibility result for one observed state transition."""

    admissible: bool
    failed_constraints: tuple[str, ...]
    elapsed_seconds: float
    start_source_id: str
    start_source_version: str
    end_source_id: str
    end_source_version: str
    envelope_source_id: str
    envelope_source_version: str
    envelope_model_version: str
    contract_version: str = AIRCRAFT_REACHABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.admissible) is not bool:
            raise TypeError("admissible must be bool")
        if type(self.failed_constraints) is not tuple:
            raise TypeError("failed_constraints must be a tuple")
        if any(type(item) is not str or not item for item in self.failed_constraints):
            raise ValueError("failed_constraints must contain non-empty strings")
        if self.admissible and self.failed_constraints:
            raise ValueError("admissible results cannot contain failed constraints")
        if not self.admissible and not self.failed_constraints:
            raise ValueError("inadmissible results must contain failed constraints")
        if self.elapsed_seconds <= 0.0:
            raise ValueError("elapsed_seconds must be positive")
        if self.contract_version != AIRCRAFT_REACHABILITY_CONTRACT_VERSION:
            raise ValueError("contract_version must be AIRCRAFT-REACHABILITY-1")

    def to_payload(self) -> dict[str, Any]:
        return {
            "admissible": self.admissible,
            "contract_version": self.contract_version,
            "elapsed_seconds": float(self.elapsed_seconds),
            "end_source_id": self.end_source_id,
            "end_source_version": self.end_source_version,
            "envelope_model_version": self.envelope_model_version,
            "envelope_source_id": self.envelope_source_id,
            "envelope_source_version": self.envelope_source_version,
            "failed_constraints": list(self.failed_constraints),
            "start_source_id": self.start_source_id,
            "start_source_version": self.start_source_version,
        }


def evaluate_reachability(
    start: AircraftStateInput,
    end: AircraftStateInput,
    envelope: AircraftOperatingEnvelope,
) -> ReachabilityResult:
    """Evaluate whether one observed transition is admissible."""
    if type(start) is not AircraftStateInput:
        raise TypeError("start must be AircraftStateInput")
    if type(end) is not AircraftStateInput:
        raise TypeError("end must be AircraftStateInput")
    if type(envelope) is not AircraftOperatingEnvelope:
        raise TypeError("envelope must be AircraftOperatingEnvelope")
    if start.contract_version != AIRCRAFT_STATE_CONTRACT_VERSION:
        raise ValueError("start state contract version is not supported")
    if end.contract_version != AIRCRAFT_STATE_CONTRACT_VERSION:
        raise ValueError("end state contract version is not supported")
    if envelope.contract_version != AIRCRAFT_ENVELOPE_CONTRACT_VERSION:
        raise ValueError("envelope contract version is not supported")
    if envelope.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("operating envelope must be ADMITTED")

    start_time = _parse_timestamp(start.timestamp_utc)
    end_time = _parse_timestamp(end.timestamp_utc)
    elapsed_seconds = (end_time - start_time).total_seconds()
    if elapsed_seconds <= 0.0:
        raise ValueError("end timestamp must be later than start timestamp")

    failures: list[str] = []

    if not (
        envelope.minimum_speed_mps
        <= end.groundspeed_mps
        <= envelope.maximum_speed_mps
    ):
        failures.append("END_SPEED_OUTSIDE_ENVELOPE")
    if not (
        envelope.minimum_altitude_m
        <= end.altitude_m
        <= envelope.maximum_altitude_m
    ):
        failures.append("END_ALTITUDE_OUTSIDE_ENVELOPE")

    altitude_delta = end.altitude_m - start.altitude_m
    if altitude_delta > envelope.maximum_climb_rate_mps * elapsed_seconds:
        failures.append("CLIMB_RATE_EXCEEDED")
    if -altitude_delta > envelope.maximum_descent_rate_mps * elapsed_seconds:
        failures.append("DESCENT_RATE_EXCEEDED")

    heading_delta = _shortest_heading_delta(start.heading_deg, end.heading_deg)
    if abs(heading_delta) > envelope.maximum_turn_rate_deg_s * elapsed_seconds:
        failures.append("TURN_RATE_EXCEEDED")

    return ReachabilityResult(
        admissible=not failures,
        failed_constraints=tuple(failures),
        elapsed_seconds=elapsed_seconds,
        start_source_id=start.source_id,
        start_source_version=start.source_version,
        end_source_id=end.source_id,
        end_source_version=end.source_version,
        envelope_source_id=envelope.source_id,
        envelope_source_version=envelope.source_version,
        envelope_model_version=envelope.model_version,
    )
