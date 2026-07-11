"""Immutable contracts for deterministic L3.0 evidence consumption."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.evidence.registration_models import (
    CONTRACT_VERSION as REGISTRATION_CONTRACT_VERSION,
)
from mh370_inverse_inference.evidence.registration_models import RegisteredEvidenceRecord

CONTRACT_VERSION = "L3.0"
OPERATION = "registered_evidence_consumption"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ConsumptionStatus(StrEnum):
    """Final registered-evidence consumption outcome."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ConsumptionReason(StrEnum):
    """Stable machine-readable consumption reasons."""

    OK = "OK"
    REGISTRY_ID_MISMATCH = "REGISTRY_ID_MISMATCH"
    MALFORMED_REGISTERED_IDENTITY = "MALFORMED_REGISTERED_IDENTITY"
    UNSUPPORTED_CONTRACT_VERSION = "UNSUPPORTED_CONTRACT_VERSION"
    MISSING_REQUIRED_IDENTITY = "MISSING_REQUIRED_IDENTITY"
    PROJECTION_INCONSISTENT = "PROJECTION_INCONSISTENT"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class RegisteredEvidenceProjection:
    """Read-only projection created only from registered evidence authority."""

    registry_evidence_id: str
    evidence_id: str
    observation_id: str
    source_id: str
    evidence_hash: str
    validation_hash: str
    registration_contract_version: str

    @classmethod
    def from_registered_record(
        cls,
        record: RegisteredEvidenceRecord,
    ) -> RegisteredEvidenceProjection:
        """Reduce one authoritative registry record into a downstream projection."""
        if not isinstance(record, RegisteredEvidenceRecord):
            raise TypeError("record must be RegisteredEvidenceRecord")
        projection = object.__new__(cls)
        object.__setattr__(
            projection,
            "registry_evidence_id",
            record.registry_evidence_id,
        )
        object.__setattr__(projection, "evidence_id", record.evidence_id)
        object.__setattr__(projection, "observation_id", record.observation_id)
        object.__setattr__(projection, "source_id", record.source_id)
        object.__setattr__(projection, "evidence_hash", record.evidence_hash)
        object.__setattr__(projection, "validation_hash", record.validation_hash)
        object.__setattr__(
            projection,
            "registration_contract_version",
            record.registration_contract_version,
        )
        return projection

    def to_payload(self) -> dict[str, str]:
        """Return the canonical downstream projection payload."""
        return {
            "evidence_hash": self.evidence_hash,
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "registration_contract_version": self.registration_contract_version,
            "registry_evidence_id": self.registry_evidence_id,
            "source_id": self.source_id,
            "validation_hash": self.validation_hash,
        }


@dataclass(frozen=True, slots=True)
class AcceptedEvidenceProjection:
    """Immutable authority-bearing input for later interpretation layers."""

    registry_evidence_id: str
    evidence_id: str
    observation_id: str
    source_id: str
    evidence_hash: str
    validation_hash: str
    consumption_contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _sha256(self.registry_evidence_id, "registry_evidence_id")
        _non_empty(self.evidence_id, "evidence_id")
        _non_empty(self.observation_id, "observation_id")
        _non_empty(self.source_id, "source_id")
        _sha256(self.evidence_hash, "evidence_hash")
        _sha256(self.validation_hash, "validation_hash")
        if self.consumption_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"consumption_contract_version must be {CONTRACT_VERSION}"
            )

    @classmethod
    def from_projection(
        cls,
        projection: RegisteredEvidenceProjection,
    ) -> AcceptedEvidenceProjection:
        """Create the accepted downstream type from an admitted projection."""
        return cls(
            registry_evidence_id=projection.registry_evidence_id,
            evidence_id=projection.evidence_id,
            observation_id=projection.observation_id,
            source_id=projection.source_id,
            evidence_hash=projection.evidence_hash,
            validation_hash=projection.validation_hash,
        )

    def to_payload(self) -> dict[str, str]:
        """Return the canonical accepted-projection payload."""
        return {
            "consumption_contract_version": self.consumption_contract_version,
            "evidence_hash": self.evidence_hash,
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "registry_evidence_id": self.registry_evidence_id,
            "source_id": self.source_id,
            "validation_hash": self.validation_hash,
        }


@dataclass(frozen=True, slots=True)
class EvidenceConsumptionRequest:
    """Complete deterministic request for the L3.0 projection gate."""

    evidence: RegisteredEvidenceProjection
    expected_registry_evidence_id: str
    expected_contract_version: str
    consumption_policy_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, RegisteredEvidenceProjection):
            raise TypeError("evidence must be RegisteredEvidenceProjection")
        _sha256(
            self.expected_registry_evidence_id,
            "expected_registry_evidence_id",
        )
        _non_empty(self.expected_contract_version, "expected_contract_version")
        _non_empty(self.consumption_policy_version, "consumption_policy_version")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical consumption-request payload."""
        return {
            "consumption_policy_version": self.consumption_policy_version,
            "evidence": self.evidence.to_payload(),
            "expected_contract_version": self.expected_contract_version,
            "expected_registry_evidence_id": self.expected_registry_evidence_id,
        }


@dataclass(frozen=True, slots=True)
class EvidenceConsumptionResult:
    """Immutable consumption outcome with exact deterministic identities."""

    status: ConsumptionStatus
    reason_codes: tuple[ConsumptionReason, ...]
    accepted_projection: AcceptedEvidenceProjection | None
    input_hash: str
    output_hash: str
    op_signature_hash: str
    consumption_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        _non_empty(self.consumption_policy_version, "consumption_policy_version")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        if self.status is ConsumptionStatus.ACCEPTED and self.accepted_projection is None:
            raise ValueError("accepted result requires accepted_projection")
        if (
            self.status is ConsumptionStatus.REJECTED
            and self.accepted_projection is not None
        ):
            raise ValueError("rejected result cannot include accepted_projection")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical consumption-result payload."""
        return {
            "accepted_projection": (
                None
                if self.accepted_projection is None
                else self.accepted_projection.to_payload()
            ),
            "consumption_policy_version": self.consumption_policy_version,
            "input_hash": self.input_hash,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "status": self.status.value,
        }


def projection_is_well_formed(projection: RegisteredEvidenceProjection) -> bool:
    """Return whether a projection retains a valid registered identity shape."""
    try:
        _sha256(projection.registry_evidence_id, "registry_evidence_id")
        _non_empty(projection.evidence_id, "evidence_id")
        _non_empty(projection.observation_id, "observation_id")
        _non_empty(projection.source_id, "source_id")
        _sha256(projection.evidence_hash, "evidence_hash")
        _sha256(projection.validation_hash, "validation_hash")
    except (AttributeError, TypeError, ValueError):
        return False
    return projection.registration_contract_version == REGISTRATION_CONTRACT_VERSION
