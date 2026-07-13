"""Immutable deterministic L6.3 comparative assessment trace contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.comparative.record import ComparativeAssessmentRecord
from mh370_inverse_inference.comparative.result import ComparativeAssessmentResult
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L6.3"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ComparativeAssessmentTrace:
    """Content-addressed ordered trace over one exact L6.2 result."""

    comparative_result_hash: str
    comparative_request_hash: str
    ordered_record_hashes: tuple[str, ...]
    comparative_trace_contract_version: str
    trace_hash: str

    @classmethod
    def _from_result(
        cls,
        result: ComparativeAssessmentResult,
        *,
        records: tuple[ComparativeAssessmentRecord, ...],
    ) -> ComparativeAssessmentTrace:
        record_hashes = tuple(record.record_hash for record in records)
        canonical_payload: dict[str, Any] = {
            "comparative_request_hash": result.comparative_request_hash,
            "comparative_result_hash": result.result_hash,
            "comparative_trace_contract_version": CONTRACT_VERSION,
            "ordered_record_hashes": list(record_hashes),
        }
        trace = object.__new__(cls)
        object.__setattr__(trace, "comparative_result_hash", result.result_hash)
        object.__setattr__(
            trace,
            "comparative_request_hash",
            result.comparative_request_hash,
        )
        object.__setattr__(trace, "ordered_record_hashes", record_hashes)
        object.__setattr__(
            trace,
            "comparative_trace_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(trace, "trace_hash", sha256_payload(canonical_payload))
        trace._validate()
        return trace

    def _validate(self) -> None:
        _sha256(self.comparative_result_hash, "comparative_result_hash")
        _sha256(self.comparative_request_hash, "comparative_request_hash")
        for record_hash in self.ordered_record_hashes:
            _sha256(record_hash, "ordered_record_hashes item")
        if len(set(self.ordered_record_hashes)) != len(self.ordered_record_hashes):
            raise ValueError("ordered_record_hashes cannot contain duplicates")
        if self.comparative_trace_contract_version != CONTRACT_VERSION:
            raise ValueError("comparative_trace_contract_version is invalid")
        _sha256(self.trace_hash, "trace_hash")
        if self.trace_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("trace_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which trace_hash is derived."""
        return {
            "comparative_request_hash": self.comparative_request_hash,
            "comparative_result_hash": self.comparative_result_hash,
            "comparative_trace_contract_version": (
                self.comparative_trace_contract_version
            ),
            "ordered_record_hashes": list(self.ordered_record_hashes),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical trace payload with its content identity."""
        return {**self.canonical_payload(), "trace_hash": self.trace_hash}


def build_comparative_assessment_trace(
    result: ComparativeAssessmentResult,
    *,
    records: tuple[ComparativeAssessmentRecord, ...],
) -> ComparativeAssessmentTrace:
    """Bind one exact L6.2 result to its ordered L6.1 record identities."""
    if type(result) is not ComparativeAssessmentResult:
        raise TypeError("result must be ComparativeAssessmentResult")
    if any(type(record) is not ComparativeAssessmentRecord for record in records):
        raise TypeError("records must contain ComparativeAssessmentRecord values")
    if any(
        record.comparative_request_hash != result.comparative_request_hash
        for record in records
    ):
        raise ValueError("records must reference the result comparative request")
    record_hashes = tuple(record.record_hash for record in records)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    if record_hashes != result.ordered_record_hashes:
        raise ValueError("records must preserve comparative-result order")
    return ComparativeAssessmentTrace._from_result(result, records=records)
