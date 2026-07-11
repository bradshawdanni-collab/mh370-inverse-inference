"""Immutable contracts for deterministic L2.1 evidence assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.observations.models import (
    ObservationAdmissionResult,
    ObservationType,
)

CONTRACT_VERSION = "L2.1"
OPERATION = "observation_evidence_assembly"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceAssemblyStatus(StrEnum):
    """Final evidence-assembly outcome."""

    ASSEMBLED = "ASSEMBLED"
    REJECTED = "REJECTED"


class EvidenceAssemblyReason(StrEnum):
    """Stable machine-readable evidence-assembly reasons."""

    OK = "OK"
    SOURCE_NOT_ADMITTED = "SOURCE_NOT_ADMITTED"
    INVALID_ADMISSION_IDENTITY = "INVALID_ADMISSION_IDENTITY"
    INVALID_PROVENANCE_CHAIN = "INVALID_PROVENANCE_CHAIN"
    MISSING_PROVENANCE_LINK = "MISSING_PROVENANCE_LINK"
    INVALID_SOURCE_HASH = "INVALID_SOURCE_HASH"
    MODEL_VERSION_MISMATCH = "MODEL_VERSION_MISMATCH"
    CONTRACT_VERSION_MISMATCH = "CONTRACT_VERSION_MISMATCH"


def _non_empty(value: str, name: str) -> str:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")
    return value


def _sha256(value: str, name: str) -> str:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceProvenanceLink:
    """One immutable ordered link in the evidence provenance chain."""

    link_index: int
    subject_id: str
    predicate: str
    object_id: str
    subject_hash: str
    object_hash: str
    source_reference: str

    def __post_init__(self) -> None:
        if self.link_index < 0:
            raise ValueError("link_index cannot be negative")
        _non_empty(self.subject_id, "subject_id")
        _non_empty(self.predicate, "predicate")
        _non_empty(self.object_id, "object_id")
        _non_empty(self.source_reference, "source_reference")
        _sha256(self.subject_hash, "subject_hash")
        _sha256(self.object_hash, "object_hash")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical provenance-link payload."""
        return {
            "link_index": self.link_index,
            "object_hash": self.object_hash,
            "object_id": self.object_id,
            "predicate": self.predicate,
            "source_reference": self.source_reference,
            "subject_hash": self.subject_hash,
            "subject_id": self.subject_id,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable evidence package preserving admitted observation identity."""

    evidence_id: str
    observation_id: str
    observation_type: ObservationType
    observation_hash: str
    source_id: str
    source_hash: str
    provenance_chain: tuple[EvidenceProvenanceLink, ...]
    assembled_at_policy_version: str
    model_version: str
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.evidence_id, "evidence_id")
        _non_empty(self.observation_id, "observation_id")
        _non_empty(self.source_id, "source_id")
        _non_empty(self.assembled_at_policy_version, "assembled_at_policy_version")
        _non_empty(self.model_version, "model_version")
        _sha256(self.observation_hash, "observation_hash")
        _sha256(self.source_hash, "source_hash")
        if self.contract_version != CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {CONTRACT_VERSION}")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical evidence-record payload."""
        return {
            "assembled_at_policy_version": self.assembled_at_policy_version,
            "contract_version": self.contract_version,
            "evidence_id": self.evidence_id,
            "model_version": self.model_version,
            "observation_hash": self.observation_hash,
            "observation_id": self.observation_id,
            "observation_type": self.observation_type.value,
            "provenance_chain": [
                link.to_payload() for link in self.provenance_chain
            ],
            "source_hash": self.source_hash,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class EvidenceAssemblyRequest:
    """Complete deterministic request for evidence assembly."""

    admission_result: ObservationAdmissionResult
    provenance_chain: tuple[EvidenceProvenanceLink, ...]
    evidence_id: str
    expected_model_version: str
    expected_contract_version: str
    assembly_policy_version: str

    def __post_init__(self) -> None:
        _non_empty(self.evidence_id, "evidence_id")
        _non_empty(self.expected_model_version, "expected_model_version")
        _non_empty(self.expected_contract_version, "expected_contract_version")
        _non_empty(self.assembly_policy_version, "assembly_policy_version")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical assembly-request payload."""
        return {
            "admission_result": self.admission_result.to_payload(),
            "assembly_policy_version": self.assembly_policy_version,
            "evidence_id": self.evidence_id,
            "expected_contract_version": self.expected_contract_version,
            "expected_model_version": self.expected_model_version,
            "provenance_chain": [
                link.to_payload() for link in self.provenance_chain
            ],
        }


@dataclass(frozen=True, slots=True)
class EvidenceAssemblyResult:
    """Immutable evidence-assembly outcome with exact identity hashes."""

    status: EvidenceAssemblyStatus
    reason_codes: tuple[EvidenceAssemblyReason, ...]
    evidence_record: EvidenceRecord | None
    admission_result: ObservationAdmissionResult
    input_hash: str
    output_hash: str
    op_signature_hash: str
    assembly_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        _non_empty(self.assembly_policy_version, "assembly_policy_version")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        if (
            self.status is EvidenceAssemblyStatus.ASSEMBLED
            and self.evidence_record is None
        ):
            raise ValueError("assembled result requires evidence_record")
        if (
            self.status is EvidenceAssemblyStatus.REJECTED
            and self.evidence_record is not None
        ):
            raise ValueError("rejected result cannot include evidence_record")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical evidence-assembly result payload."""
        return {
            "admission_result": self.admission_result.to_payload(),
            "assembly_policy_version": self.assembly_policy_version,
            "evidence_record": (
                None
                if self.evidence_record is None
                else self.evidence_record.to_payload()
            ),
            "input_hash": self.input_hash,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "status": self.status.value,
        }
