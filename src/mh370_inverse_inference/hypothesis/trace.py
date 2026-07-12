"""Immutable deterministic L5.4 hypothesis evaluation trace contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis.relation import (
    EvidenceHypothesisRelationRecord,
)
from mh370_inverse_inference.hypothesis.result import HypothesisEvaluationResult

CONTRACT_VERSION = "L5.4"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class HypothesisEvaluationTrace:
    """Content-addressed ordered trace over one exact L5.3 result."""

    evaluation_result_hash: str
    ordered_relation_record_hashes: tuple[str, ...]
    trace_contract_version: str
    trace_hash: str

    @classmethod
    def _from_evaluation_result(
        cls,
        result: HypothesisEvaluationResult,
        *,
        records: tuple[EvidenceHypothesisRelationRecord, ...],
    ) -> HypothesisEvaluationTrace:
        ordered_hashes = tuple(record.record_hash for record in records)
        canonical_payload: dict[str, Any] = {
            "evaluation_result_hash": result.result_hash,
            "ordered_relation_record_hashes": list(ordered_hashes),
            "trace_contract_version": CONTRACT_VERSION,
        }
        trace = object.__new__(cls)
        object.__setattr__(trace, "evaluation_result_hash", result.result_hash)
        object.__setattr__(trace, "ordered_relation_record_hashes", ordered_hashes)
        object.__setattr__(trace, "trace_contract_version", CONTRACT_VERSION)
        object.__setattr__(trace, "trace_hash", sha256_payload(canonical_payload))
        trace._validate()
        return trace

    def _validate(self) -> None:
        _sha256(self.evaluation_result_hash, "evaluation_result_hash")
        for record_hash in self.ordered_relation_record_hashes:
            _sha256(record_hash, "ordered_relation_record_hashes item")
        if len(set(self.ordered_relation_record_hashes)) != len(
            self.ordered_relation_record_hashes
        ):
            raise ValueError("ordered_relation_record_hashes cannot contain duplicates")
        if self.trace_contract_version != CONTRACT_VERSION:
            raise ValueError("trace_contract_version is invalid")
        _sha256(self.trace_hash, "trace_hash")
        if self.trace_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("trace_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which trace_hash is derived."""
        return {
            "evaluation_result_hash": self.evaluation_result_hash,
            "ordered_relation_record_hashes": list(self.ordered_relation_record_hashes),
            "trace_contract_version": self.trace_contract_version,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical trace payload with its content identity."""
        return {**self.canonical_payload(), "trace_hash": self.trace_hash}


def build_hypothesis_evaluation_trace(
    result: HypothesisEvaluationResult,
    *,
    records: tuple[EvidenceHypothesisRelationRecord, ...],
) -> HypothesisEvaluationTrace:
    """Bind one L5.3 result to ordered L5.2 relation-record identities."""
    if type(result) is not HypothesisEvaluationResult:
        raise TypeError("result must be HypothesisEvaluationResult")
    if any(type(record) is not EvidenceHypothesisRelationRecord for record in records):
        raise TypeError("records must contain EvidenceHypothesisRelationRecord values")
    result_hashes = set(result.ordered_relation_record_hashes)
    if any(record.record_hash not in result_hashes for record in records):
        raise ValueError("records must be included in the supplied evaluation result")
    record_hashes = tuple(record.record_hash for record in records)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    if record_hashes != result.ordered_relation_record_hashes:
        raise ValueError("records must preserve evaluation-result order")
    return HypothesisEvaluationTrace._from_evaluation_result(
        result,
        records=records,
    )
