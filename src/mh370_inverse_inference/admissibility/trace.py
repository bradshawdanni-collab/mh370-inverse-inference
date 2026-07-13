"""Immutable deterministic L7.3 admissibility decision trace contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.admissibility.record import AdmissibilityDecisionRecord
from mh370_inverse_inference.admissibility.result import AdmissibilityDecisionResult
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L7.3"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class AdmissibilityDecisionTrace:
    """Content-addressed ordered trace over one exact L7.2 result."""

    admissibility_result_hash: str
    admissibility_request_hash: str
    ordered_record_hashes: tuple[str, ...]
    admissibility_trace_contract_version: str
    trace_hash: str

    @classmethod
    def _from_result(
        cls,
        result: AdmissibilityDecisionResult,
        *,
        records: tuple[AdmissibilityDecisionRecord, ...],
    ) -> AdmissibilityDecisionTrace:
        record_hashes = tuple(record.record_hash for record in records)
        canonical_payload: dict[str, Any] = {
            "admissibility_request_hash": result.admissibility_request_hash,
            "admissibility_result_hash": result.result_hash,
            "admissibility_trace_contract_version": CONTRACT_VERSION,
            "ordered_record_hashes": list(record_hashes),
        }
        trace = object.__new__(cls)
        object.__setattr__(trace, "admissibility_result_hash", result.result_hash)
        object.__setattr__(
            trace,
            "admissibility_request_hash",
            result.admissibility_request_hash,
        )
        object.__setattr__(trace, "ordered_record_hashes", record_hashes)
        object.__setattr__(
            trace,
            "admissibility_trace_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(trace, "trace_hash", sha256_payload(canonical_payload))
        trace._validate()
        return trace

    def _validate(self) -> None:
        _sha256(self.admissibility_result_hash, "admissibility_result_hash")
        _sha256(self.admissibility_request_hash, "admissibility_request_hash")
        for record_hash in self.ordered_record_hashes:
            _sha256(record_hash, "ordered_record_hashes item")
        if len(set(self.ordered_record_hashes)) != len(self.ordered_record_hashes):
            raise ValueError("ordered_record_hashes cannot contain duplicates")
        if self.admissibility_trace_contract_version != CONTRACT_VERSION:
            raise ValueError("admissibility_trace_contract_version is invalid")
        _sha256(self.trace_hash, "trace_hash")
        if self.trace_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("trace_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which trace_hash is derived."""
        return {
            "admissibility_request_hash": self.admissibility_request_hash,
            "admissibility_result_hash": self.admissibility_result_hash,
            "admissibility_trace_contract_version": (
                self.admissibility_trace_contract_version
            ),
            "ordered_record_hashes": list(self.ordered_record_hashes),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical trace payload with its content identity."""
        return {**self.canonical_payload(), "trace_hash": self.trace_hash}


def build_admissibility_decision_trace(
    result: AdmissibilityDecisionResult,
    *,
    records: tuple[AdmissibilityDecisionRecord, ...],
) -> AdmissibilityDecisionTrace:
    """Bind one exact L7.2 result to its ordered L7.1 record identities."""
    if type(result) is not AdmissibilityDecisionResult:
        raise TypeError("result must be AdmissibilityDecisionResult")
    if any(type(record) is not AdmissibilityDecisionRecord for record in records):
        raise TypeError("records must contain AdmissibilityDecisionRecord values")
    if any(
        record.admissibility_request_hash != result.admissibility_request_hash
        for record in records
    ):
        raise ValueError("records must reference the result admissibility request")
    record_hashes = tuple(record.record_hash for record in records)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    if record_hashes != result.ordered_record_hashes:
        raise ValueError("records must preserve admissibility-result order")
    return AdmissibilityDecisionTrace._from_result(result, records=records)
