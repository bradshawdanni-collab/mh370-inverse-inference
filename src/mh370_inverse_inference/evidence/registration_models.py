"""Immutable contracts for deterministic L2.3 evidence registration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.evidence.validation_models import EvidenceValidationResult

CONTRACT_VERSION = "L2.3"
OPERATION = "evidence_registration"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceRegistrationStatus(StrEnum):
    """Final evidence-registration outcome."""

    REGISTERED = "REGISTERED"
    REJECTED = "REJECTED"


class EvidenceRegistrationReason(StrEnum):
    """Stable machine-readable registration reasons."""

    OK = "OK"
    VALIDATION_NOT_VALID = "VALIDATION_NOT_VALID"
    MISSING_EVIDENCE_RECORD = "MISSING_EVIDENCE_RECORD"
    CONTRACT_VERSION_MISMATCH = "CONTRACT_VERSION_MISMATCH"
    EVIDENCE_HASH_MISMATCH = "EVIDENCE_HASH_MISMATCH"
    VALIDATION_HASH_MISMATCH = "VALIDATION_HASH_MISMATCH"
    VALIDATION_RESULT_INCONSISTENT = "VALIDATION_RESULT_INCONSISTENT"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class RegisteredEvidenceRecord:
    """Immutable downstream release identity for validated evidence."""

    registry_evidence_id: str
    evidence_id: str
    observation_id: str
    source_id: str
    evidence_hash: str
    validation_hash: str
    validation_output_hash: str
    validation_operation_hash: str
    registration_contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        _sha256(self.registry_evidence_id, "registry_evidence_id")
        _non_empty(self.evidence_id, "evidence_id")
        _non_empty(self.observation_id, "observation_id")
        _non_empty(self.source_id, "source_id")
        _sha256(self.evidence_hash, "evidence_hash")
        _sha256(self.validation_hash, "validation_hash")
        _sha256(self.validation_output_hash, "validation_output_hash")
        _sha256(self.validation_operation_hash, "validation_operation_hash")
        if self.registration_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"registration_contract_version must be {CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical registered-evidence payload."""
        return {
            "evidence_hash": self.evidence_hash,
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "registration_contract_version": self.registration_contract_version,
            "registry_evidence_id": self.registry_evidence_id,
            "source_id": self.source_id,
            "validation_hash": self.validation_hash,
            "validation_operation_hash": self.validation_operation_hash,
            "validation_output_hash": self.validation_output_hash,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRegistrationRequest:
    """Complete deterministic request for evidence registration."""

    validation_result: EvidenceValidationResult
    expected_evidence_hash: str
    expected_validation_hash: str
    expected_contract_version: str
    registry_policy_version: str

    def __post_init__(self) -> None:
        _sha256(self.expected_evidence_hash, "expected_evidence_hash")
        _sha256(self.expected_validation_hash, "expected_validation_hash")
        _non_empty(self.expected_contract_version, "expected_contract_version")
        _non_empty(self.registry_policy_version, "registry_policy_version")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical registration-request payload."""
        return {
            "expected_contract_version": self.expected_contract_version,
            "expected_evidence_hash": self.expected_evidence_hash,
            "expected_validation_hash": self.expected_validation_hash,
            "registry_policy_version": self.registry_policy_version,
            "validation_result": self.validation_result.to_payload(),
        }


@dataclass(frozen=True, slots=True)
class EvidenceRegistrationResult:
    """Immutable registration outcome with exact identity hashes."""

    status: EvidenceRegistrationStatus
    reason_codes: tuple[EvidenceRegistrationReason, ...]
    registered_record: RegisteredEvidenceRecord | None
    validation_result: EvidenceValidationResult
    input_hash: str
    output_hash: str
    op_signature_hash: str
    registry_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        _non_empty(self.registry_policy_version, "registry_policy_version")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        if (
            self.status is EvidenceRegistrationStatus.REGISTERED
            and self.registered_record is None
        ):
            raise ValueError("registered result requires registered_record")
        if (
            self.status is EvidenceRegistrationStatus.REJECTED
            and self.registered_record is not None
        ):
            raise ValueError("rejected result cannot include registered_record")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical registration-result payload."""
        return {
            "input_hash": self.input_hash,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "registered_record": (
                None
                if self.registered_record is None
                else self.registered_record.to_payload()
            ),
            "registry_policy_version": self.registry_policy_version,
            "status": self.status.value,
            "validation_result": self.validation_result.to_payload(),
        }
