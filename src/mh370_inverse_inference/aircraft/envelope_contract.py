"""Immutable source-bounded aircraft operating envelope contract for L1.2."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.provenance import ArtifactAdmissionState

AIRCRAFT_ENVELOPE_CONTRACT_VERSION = "AIRCRAFT-ENVELOPE-1"

_ALLOWED_ADMISSION_STATES = (
    ArtifactAdmissionState.PROPOSED,
    ArtifactAdmissionState.ADMITTED,
)


def _finite_non_negative(value: float, name: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be numeric")
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    if resolved < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return resolved


@dataclass(frozen=True, slots=True)
class AircraftOperatingEnvelope:
    """Governed aircraft operating limits without propagation semantics."""

    minimum_speed_mps: float
    maximum_speed_mps: float
    minimum_altitude_m: float
    maximum_altitude_m: float
    maximum_climb_rate_mps: float
    maximum_descent_rate_mps: float
    maximum_turn_rate_deg_s: float
    source_id: str
    source_version: str
    model_version: str
    admission_state: ArtifactAdmissionState
    contract_version: str = AIRCRAFT_ENVELOPE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        minimum_speed_name = "minimum_speed_mps"
        maximum_speed_name = "maximum_speed_mps"
        minimum_speed = _finite_non_negative(
            self.minimum_speed_mps,
            minimum_speed_name,
        )
        maximum_speed = _finite_non_negative(
            self.maximum_speed_mps,
            maximum_speed_name,
        )
        minimum_altitude = _finite_non_negative(
            self.minimum_altitude_m,
            "minimum_altitude_m",
        )
        maximum_altitude = _finite_non_negative(
            self.maximum_altitude_m,
            "maximum_altitude_m",
        )
        _finite_non_negative(
            self.maximum_climb_rate_mps,
            "maximum_climb_rate_mps",
        )
        _finite_non_negative(
            self.maximum_descent_rate_mps,
            "maximum_descent_rate_mps",
        )
        _finite_non_negative(
            self.maximum_turn_rate_deg_s,
            "maximum_turn_rate_deg_s",
        )

        if minimum_speed > maximum_speed:
            raise ValueError("minimum_speed_mps cannot exceed maximum_speed_mps")
        if minimum_altitude > maximum_altitude:
            raise ValueError(
                "minimum_altitude_m cannot exceed maximum_altitude_m"
            )
        if not self.source_id.strip():
            raise ValueError("source_id cannot be blank")
        if not self.source_version.strip():
            raise ValueError("source_version cannot be blank")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")
        if type(self.admission_state) is not ArtifactAdmissionState:
            raise TypeError("admission_state must be ArtifactAdmissionState")
        if self.admission_state not in _ALLOWED_ADMISSION_STATES:
            raise ValueError("admission_state must be PROPOSED or ADMITTED")
        if self.contract_version != AIRCRAFT_ENVELOPE_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AIRCRAFT_ENVELOPE_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible envelope payload."""
        return {
            "admission_state": self.admission_state.value,
            "contract_version": self.contract_version,
            "maximum_altitude_m": float(self.maximum_altitude_m),
            "maximum_climb_rate_mps": float(self.maximum_climb_rate_mps),
            "maximum_descent_rate_mps": float(self.maximum_descent_rate_mps),
            "maximum_speed_mps": float(self.maximum_speed_mps),
            "maximum_turn_rate_deg_s": float(self.maximum_turn_rate_deg_s),
            "minimum_altitude_m": float(self.minimum_altitude_m),
            "minimum_speed_mps": float(self.minimum_speed_mps),
            "model_version": self.model_version,
            "source_id": self.source_id,
            "source_version": self.source_version,
        }
