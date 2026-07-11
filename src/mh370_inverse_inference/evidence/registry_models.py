"""Immutable contracts for deterministic L2.4 registry queries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.registration_models import RegisteredEvidenceRecord

CONTRACT_VERSION = "L2.4"
OPERATION = "evidence_registry_lookup"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceRegistryStatus(StrEnum):
    """Final registry-query outcome."""

    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"


class EvidenceRegistryReason(StrEnum):
    """Stable machine-readable registry-query reasons."""

    OK = "OK"
    EVIDENCE_NOT_REGISTERED = "EVIDENCE_NOT_REGISTERED"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def snapshot_identity_payload(
    records: tuple[RegisteredEvidenceRecord, ...],
) -> dict[str, Any]:
    """Return the canonical identity payload for one registry snapshot."""
    return {
        "contract_version": CONTRACT_VERSION,
        "records": [record.to_payload() for record in records],
    }


@dataclass(frozen=True, slots=True)
class EvidenceRegistrySnapshot:
    """Immutable canonically ordered registry snapshot."""

    records: tuple[RegisteredEvidenceRecord, ...]
    snapshot_hash: str

    def __post_init__(self) -> None:
        _sha256(self.snapshot_hash, "snapshot_hash")
        ids = tuple(record.registry_evidence_id for record in self.records)
        if ids != tuple(sorted(ids)):
            raise ValueError("records must be ordered by registry_evidence_id")
        if len(ids) != len(set(ids)):
            raise ValueError("registry_evidence_id values must be unique")
        expected_hash = sha256_payload(snapshot_identity_payload(self.records))
        if self.snapshot_hash != expected_hash:
            raise ValueError("snapshot_hash does not match canonical records")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical snapshot payload."""
        return {
            "records": [record.to_payload() for record in self.records],
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRegistryRequest:
    """Complete deterministic request for one registry lookup."""

    snapshot: EvidenceRegistrySnapshot
    registry_evidence_id: str
    registry_policy_version: str

    def __post_init__(self) -> None:
        _sha256(self.registry_evidence_id, "registry_evidence_id")
        _non_empty(self.registry_policy_version, "registry_policy_version")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical registry-request payload."""
        return {
            "registry_evidence_id": self.registry_evidence_id,
            "registry_policy_version": self.registry_policy_version,
            "snapshot": self.snapshot.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class RegisteredEvidenceLookup:
    """Stable projection returned by registry queries."""

    registry_evidence_id: str
    evidence_id: str
    observation_id: str
    source_id: str

    @classmethod
    def from_record(cls, record: RegisteredEvidenceRecord) -> RegisteredEvidenceLookup:
        """Create a lookup projection from a registered evidence record."""
        return cls(
            registry_evidence_id=record.registry_evidence_id,
            evidence_id=record.evidence_id,
            observation_id=record.observation_id,
            source_id=record.source_id,
        )

    def to_payload(self) -> dict[str, str]:
        """Return the canonical lookup payload."""
        return {
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "registry_evidence_id": self.registry_evidence_id,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRegistryResult:
    """Immutable registry-query result with exact identity hashes."""

    status: EvidenceRegistryStatus
    reason_codes: tuple[EvidenceRegistryReason, ...]
    lookup: RegisteredEvidenceLookup | None
    input_hash: str
    output_hash: str
    op_signature_hash: str
    snapshot_hash: str
    registry_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        _sha256(self.snapshot_hash, "snapshot_hash")
        _non_empty(self.registry_policy_version, "registry_policy_version")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        if self.status is EvidenceRegistryStatus.FOUND and self.lookup is None:
            raise ValueError("found result requires lookup")
        if self.status is EvidenceRegistryStatus.NOT_FOUND and self.lookup is not None:
            raise ValueError("not-found result cannot include lookup")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical registry-result payload."""
        return {
            "input_hash": self.input_hash,
            "lookup": None if self.lookup is None else self.lookup.to_payload(),
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "registry_policy_version": self.registry_policy_version,
            "snapshot_hash": self.snapshot_hash,
            "status": self.status.value,
        }
