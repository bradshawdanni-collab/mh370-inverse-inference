"""Governed BFO observation and calibration contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mh370_inverse_inference.provenance import ArtifactAdmissionState

BFO_CONTRACT_VERSION = "BFO-CONTRACT-1"
BFO_FREQUENCY_UNIT = "Hz"
BFO_UNCERTAINTY_UNIT = "Hz"


def _parse_timestamp(value: str) -> datetime:
    if type(value) is not str:
        raise TypeError("timestamp_utc must be a string")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")
    return parsed


def _non_empty(value: str, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    return normalized


def _finite(value: float, field: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{field} must be numeric")
    converted = float(value)
    if converted != converted or converted in (float("inf"), float("-inf")):
        raise ValueError(f"{field} must be finite")
    return converted


@dataclass(frozen=True, slots=True)
class BFOObservation:
    """One governed Burst Frequency Offset observation."""

    observation_id: str
    timestamp_utc: str
    bfo_hz: float
    uncertainty_hz: float
    source_artifact_id: str
    source_artifact_version: str
    source_citation: str
    calibration_source_id: str
    calibration_source_version: str
    admission_state: ArtifactAdmissionState
    frequency_unit: str = BFO_FREQUENCY_UNIT
    uncertainty_unit: str = BFO_UNCERTAINTY_UNIT
    contract_version: str = BFO_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.observation_id, "observation_id")
        _parse_timestamp(self.timestamp_utc)
        _finite(self.bfo_hz, "bfo_hz")
        uncertainty = _finite(self.uncertainty_hz, "uncertainty_hz")
        if uncertainty < 0.0:
            raise ValueError("uncertainty_hz cannot be negative")
        _non_empty(self.source_artifact_id, "source_artifact_id")
        _non_empty(self.source_artifact_version, "source_artifact_version")
        _non_empty(self.source_citation, "source_citation")
        _non_empty(self.calibration_source_id, "calibration_source_id")
        _non_empty(self.calibration_source_version, "calibration_source_version")
        if type(self.admission_state) is not ArtifactAdmissionState:
            raise TypeError("admission_state must be ArtifactAdmissionState")
        if self.frequency_unit != BFO_FREQUENCY_UNIT:
            raise ValueError("frequency_unit must be Hz")
        if self.uncertainty_unit != BFO_UNCERTAINTY_UNIT:
            raise ValueError("uncertainty_unit must be Hz")
        if self.contract_version != BFO_CONTRACT_VERSION:
            raise ValueError("contract_version must be BFO-CONTRACT-1")

    def to_payload(self) -> dict[str, Any]:
        return {
            "admission_state": self.admission_state.value,
            "bfo_hz": float(self.bfo_hz),
            "calibration_source_id": self.calibration_source_id,
            "calibration_source_version": self.calibration_source_version,
            "contract_version": self.contract_version,
            "frequency_unit": self.frequency_unit,
            "observation_id": self.observation_id,
            "source_artifact_id": self.source_artifact_id,
            "source_artifact_version": self.source_artifact_version,
            "source_citation": self.source_citation,
            "timestamp_utc": self.timestamp_utc,
            "uncertainty_hz": float(self.uncertainty_hz),
            "uncertainty_unit": self.uncertainty_unit,
        }
