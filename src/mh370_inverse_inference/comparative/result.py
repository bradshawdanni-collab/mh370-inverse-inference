"""Immutable deterministic L6.2 comparative assessment result contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.comparative.record import ComparativeAssessmentRecord
from mh370_inverse_inference.comparative.request import ComparativeAssessmentRequest
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L6.2"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ComparativeAssessmentStatus(StrEnum):
    """Stable aggregate status for one comparative assessment."""

    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


class ComparativeAssessmentReason(StrEnum):
    """Stable machine-readable reason for one comparative result."""

    OK = "OK"
    POLICY_REJECTED = "POLICY_REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ComparativeAssessmentResult:
    """Content-addressed aggregate result over one exact L6.0 request."""

    comparative_request_hash: str
    ordered_record_hashes: tuple[str, ...]
    status: ComparativeAssessmentStatus
    reason_codes: tuple[ComparativeAssessmentReason, ...]
    comparative_result_contract_version: str
    result_hash: str

    @classmethod
    def _from_request(
        cls,
        request: ComparativeAssessmentRequest,
        *,
        records: tuple[ComparativeAssessmentRecord, ...],
        status: ComparativeAssessmentStatus,
        reason_codes: tuple[ComparativeAssessmentReason, ...],
    ) -> ComparativeAssessmentResult:
        record_hashes = tuple(record.record_hash for record in records)
        canonical_payload: dict[str, Any] = {
            "comparative_request_hash": request.request_hash,
            "comparative_result_contract_version": CONTRACT_VERSION,
            "ordered_record_hashes": list(record_hashes),
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
        result = object.__new__(cls)
        object.__setattr__(result, "comparative_request_hash", request.request_hash)
        object.__setattr__(result, "ordered_record_hashes", record_hashes)
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "reason_codes", reason_codes)
        object.__setattr__(
            result,
            "comparative_result_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(result, "result_hash", sha256_payload(canonical_payload))
        result._validate()
        return result

    def _validate(self) -> None:
        _sha256(self.comparative_request_hash, "comparative_request_hash")
        for record_hash in self.ordered_record_hashes:
            _sha256(record_hash, "ordered_record_hashes item")
        if len(set(self.ordered_record_hashes)) != len(self.ordered_record_hashes):
            raise ValueError("ordered_record_hashes cannot contain duplicates")
        if type(self.status) is not ComparativeAssessmentStatus:
            raise TypeError("status must be ComparativeAssessmentStatus")
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        if any(
            type(reason) is not ComparativeAssessmentReason
            for reason in self.reason_codes
        ):
            raise TypeError(
                "reason_codes must contain ComparativeAssessmentReason values"
            )
        if self.comparative_result_contract_version != CONTRACT_VERSION:
            raise ValueError("comparative_result_contract_version is invalid")
        _sha256(self.result_hash, "result_hash")
        if self.result_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("result_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which result_hash is derived."""
        return {
            "comparative_request_hash": self.comparative_request_hash,
            "comparative_result_contract_version": (
                self.comparative_result_contract_version
            ),
            "ordered_record_hashes": list(self.ordered_record_hashes),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "status": self.status.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical result payload with its content identity."""
        return {**self.canonical_payload(), "result_hash": self.result_hash}


def build_comparative_assessment_result(
    request: ComparativeAssessmentRequest,
    *,
    records: tuple[ComparativeAssessmentRecord, ...],
    status: ComparativeAssessmentStatus,
    reason_codes: tuple[ComparativeAssessmentReason, ...],
) -> ComparativeAssessmentResult:
    """Aggregate ordered L6.1 records under one exact L6.0 request."""
    if type(request) is not ComparativeAssessmentRequest:
        raise TypeError("request must be ComparativeAssessmentRequest")
    if any(type(record) is not ComparativeAssessmentRecord for record in records):
        raise TypeError("records must contain ComparativeAssessmentRecord values")
    if any(
        record.comparative_request_hash != request.request_hash
        for record in records
    ):
        raise ValueError("records must reference the supplied comparative request")
    record_hashes = tuple(record.record_hash for record in records)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    if type(status) is not ComparativeAssessmentStatus:
        raise TypeError("status must be ComparativeAssessmentStatus")
    if not reason_codes:
        raise ValueError("reason_codes cannot be empty")
    if any(
        type(reason) is not ComparativeAssessmentReason for reason in reason_codes
    ):
        raise TypeError("reason_codes must contain ComparativeAssessmentReason values")
    return ComparativeAssessmentResult._from_request(
        request,
        records=records,
        status=status,
        reason_codes=reason_codes,
    )
