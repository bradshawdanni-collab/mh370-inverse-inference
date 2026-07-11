"""Immutable contracts for deterministic L2.2 evidence validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.evidence.models import EvidenceAssemblyResult

CONTRACT_VERSION = "L2.2"
OPERATION = "evidence_validation"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceValidationStatus(StrEnum):
    """Final evidence-validation outcome."""

    VALID = "VALID"
    REJECTED = "REJECTED"


class EvidenceValidationReason(StrEnum):
    """Stable machine-readable validation reasons."""

    OK = "OK"
    ASSEMBLY_NOT_COMPLETE = "ASSEMBLY_NOT_COMPLETE"
    MISSING_EVIDENCE_RECORD = "MISSING_EVIDENCE_RECORD"
    CONTRACT_VERSION_MISMATCH = "CONTRACT_VERSION_MISMATCH"
    EVIDENCE_HASH_MISMATCH = "EVIDENCE_HASH_MISMATCH"
    OBSERVATION_IDENTITY_MISMATCH = "OBSERVATION_IDENTITY_MISMATCH"
    SOURCE_IDENTITY_MISMATCH = "SOURCE_IDENTITY_MISMATCH"
    INVALID_PROVENANCE_CHAIN = "INVALID_PROVENANCE_CHAIN"
    PROVENANCE_HASH_DISCONTINUITY = "PROVENANCE_HASH_DISCONTINUITY"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class EvidenceValidationRequest:
    """Complete deterministic request for evidence-package validation."""

    assembly_result: EvidenceAssemblyResult
    expected_evidence_hash: str
    expected_contract_version: str
    validation_policy_version: str

    def __post_init__(self) -> None:
        _sha256(self.expected_evidence_hash, "expected_evidence_hash")
        _non_empty(self.expected_contract_version, "expected_contract_version")
        _non_empty(self.validation_policy_version, "validation_policy_version")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical validation-request payload."""
        return {
            "assembly_result": self.assembly_result.to_payload(),
            "expected_contract_version": self.expected_contract_version,
            "expected_evidence_hash": self.expected_evidence_hash,
            "validation_policy_version": self.validation_policy_version,
        }


@dataclass(frozen=True, slots=True)
class EvidenceValidationResult:
    """Immutable evidence-validation outcome with exact identity hashes."""

    status: EvidenceValidationStatus
    reason_codes: tuple[EvidenceValidationReason, ...]
    assembly_result: EvidenceAssemblyResult
    input_hash: str
    output_hash: str
    op_signature_hash: str
    validation_policy_version: str
    operation: str = OPERATION

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        _non_empty(self.validation_policy_version, "validation_policy_version")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical validation-result payload."""
        return {
            "assembly_result": self.assembly_result.to_payload(),
            "input_hash": self.input_hash,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "status": self.status.value,
            "validation_policy_version": self.validation_policy_version,
        }
