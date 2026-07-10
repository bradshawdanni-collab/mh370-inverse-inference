"""Immutable contracts for canonical observation admission."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

CONTRACT_VERSION = "L2.0"
OPERATION = "observation_admission"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ObservationType(StrEnum):
    """Supported observation categories at the admission boundary."""

    BTO = "BTO"
    BFO = "BFO"
    RADAR_POSITION = "RADAR_POSITION"
    RADAR_SPEED = "RADAR_SPEED"
    RADAR_HEADING = "RADAR_HEADING"
    OTHER = "OTHER"


class ProvenanceStatus(StrEnum):
    """Explicit source-provenance state."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    MISSING = "MISSING"


class AdmissionStatus(StrEnum):
    """Final observation-admission outcome."""

    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class AdmissionReason(StrEnum):
    """Stable machine-readable admission reasons."""

    OK = "OK"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    NON_FINITE_VALUE = "NON_FINITE_VALUE"
    INVALID_UNITS = "INVALID_UNITS"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    INVALID_UNCERTAINTY = "INVALID_UNCERTAINTY"
    MISSING_SOURCE = "MISSING_SOURCE"
    INVALID_SOURCE_HASH = "INVALID_SOURCE_HASH"
    UNVERIFIED_PROVENANCE = "UNVERIFIED_PROVENANCE"
    UNSUPPORTED_OBSERVATION_TYPE = "UNSUPPORTED_OBSERVATION_TYPE"
    MODEL_VERSION_MISMATCH = "MODEL_VERSION_MISMATCH"
    CONTRACT_VERSION_MISMATCH = "CONTRACT_VERSION_MISMATCH"


def _non_empty(value: str, name: str) -> str:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")
    return value


def _utc_timestamp(value: str, name: str) -> str:
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0.0:
        raise ValueError(f"{name} must be UTC")
    return value


@dataclass(frozen=True, slots=True)
class ObservationUncertainty:
    """Explicit uncertainty attached to an observation."""

    standard_uncertainty: float | None
    confidence_level: float | None
    uncertainty_model: str
    units: str

    def __post_init__(self) -> None:
        _non_empty(self.uncertainty_model, "uncertainty_model")
        _non_empty(self.units, "uncertainty units")

    def to_payload(self) -> dict[str, Any]:
        return {
            "confidence_level": self.confidence_level,
            "standard_uncertainty": self.standard_uncertainty,
            "uncertainty_model": self.uncertainty_model,
            "units": self.units,
        }


@dataclass(frozen=True, slots=True)
class ObservationSource:
    """Explicit source identity and provenance metadata."""

    source_id: str
    source_type: str
    publisher: str
    reference_uri: str
    retrieved_at_utc: str
    content_hash: str
    provenance_status: ProvenanceStatus

    def __post_init__(self) -> None:
        _non_empty(self.source_id, "source_id")
        _non_empty(self.source_type, "source_type")
        _non_empty(self.publisher, "publisher")
        _non_empty(self.reference_uri, "reference_uri")
        _utc_timestamp(self.retrieved_at_utc, "retrieved_at_utc")

    @property
    def has_valid_hash(self) -> bool:
        return bool(_SHA256.fullmatch(self.content_hash))

    def to_payload(self) -> dict[str, Any]:
        return {
            "content_hash": self.content_hash,
            "provenance_status": self.provenance_status.value,
            "publisher": self.publisher,
            "reference_uri": self.reference_uri,
            "retrieved_at_utc": self.retrieved_at_utc,
            "source_id": self.source_id,
            "source_type": self.source_type,
        }


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    """Canonical observation record before admission interpretation."""

    observation_id: str
    observation_type: ObservationType
    timestamp_utc: str
    measured_value: float
    units: str
    source_id: str
    uncertainty: ObservationUncertainty
    model_version: str
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.observation_id, "observation_id")
        _non_empty(self.units, "units")
        _non_empty(self.source_id, "source_id")
        _non_empty(self.model_version, "model_version")

    @property
    def has_finite_value(self) -> bool:
        return math.isfinite(float(self.measured_value))

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "measured_value": self.measured_value,
            "model_version": self.model_version,
            "observation_id": self.observation_id,
            "observation_type": self.observation_type.value,
            "source_id": self.source_id,
            "timestamp_utc": self.timestamp_utc,
            "uncertainty": self.uncertainty.to_payload(),
            "units": self.units,
        }


@dataclass(frozen=True, slots=True)
class ObservationAdmissionRequest:
    """Complete deterministic request for one admission decision."""

    observation: ObservationRecord
    source: ObservationSource | None
    expected_model_version: str
    expected_contract_version: str
    admission_policy_version: str

    def __post_init__(self) -> None:
        _non_empty(self.expected_model_version, "expected_model_version")
        _non_empty(self.expected_contract_version, "expected_contract_version")
        _non_empty(self.admission_policy_version, "admission_policy_version")

    def to_payload(self) -> dict[str, Any]:
        return {
            "admission_policy_version": self.admission_policy_version,
            "expected_contract_version": self.expected_contract_version,
            "expected_model_version": self.expected_model_version,
            "observation": self.observation.to_payload(),
            "source": None if self.source is None else self.source.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class ObservationAdmissionResult:
    """Immutable admission outcome and exact identity hashes."""

    status: AdmissionStatus
    reason_codes: tuple[AdmissionReason, ...]
    observation: ObservationRecord
    source: ObservationSource | None
    input_hash: str
    output_hash: str
    op_signature_hash: str
    admission_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        for name in ("input_hash", "output_hash", "op_signature_hash"):
            if not _SHA256.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")

    def to_payload(self) -> dict[str, Any]:
        return {
            "admission_policy_version": self.admission_policy_version,
            "input_hash": self.input_hash,
            "observation": self.observation.to_payload(),
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "source": None if self.source is None else self.source.to_payload(),
            "status": self.status.value,
        }
