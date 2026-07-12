"""Immutable deterministic L5.3 hypothesis evaluation result contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis.relation import (
    EvidenceHypothesisRelationRecord,
    EvidenceHypothesisRelationType,
)
from mh370_inverse_inference.hypothesis.request import HypothesisEvaluationRequest

CONTRACT_VERSION = "L5.3"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class HypothesisEvaluationOutcome(StrEnum):
    """Stable structural disposition for one evaluated hypothesis."""

    RETAINED = "RETAINED"
    REJECTED = "REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_BLOCKED = "CONSTRAINT_BLOCKED"


class HypothesisEvaluationStatus(StrEnum):
    """Stable aggregate status for one L5.3 evaluation result."""

    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


class HypothesisEvaluationReason(StrEnum):
    """Stable machine-readable reasons for one L5.3 result."""

    OK = "OK"
    POLICY_REJECTED = "POLICY_REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class HypothesisEvaluationResult:
    """Content-addressed structural result over one exact L5.0 request."""

    request_hash: str
    evaluation_policy_version: str
    ordered_hypothesis_ids: tuple[str, ...]
    ordered_relation_record_hashes: tuple[str, ...]
    ordered_outcomes: tuple[HypothesisEvaluationOutcome, ...]
    status: HypothesisEvaluationStatus
    reason_codes: tuple[HypothesisEvaluationReason, ...]
    evaluation_result_contract_version: str
    result_hash: str

    @classmethod
    def _from_request(
        cls,
        request: HypothesisEvaluationRequest,
        *,
        relations: tuple[EvidenceHypothesisRelationRecord, ...],
        ordered_outcomes: tuple[HypothesisEvaluationOutcome, ...],
        status: HypothesisEvaluationStatus,
        reason_codes: tuple[HypothesisEvaluationReason, ...],
    ) -> HypothesisEvaluationResult:
        record_hashes = tuple(record.record_hash for record in relations)
        canonical_payload: dict[str, Any] = {
            "evaluation_policy_version": request.evaluation_policy_version,
            "evaluation_result_contract_version": CONTRACT_VERSION,
            "ordered_hypothesis_ids": list(request.ordered_hypothesis_ids),
            "ordered_outcomes": [outcome.value for outcome in ordered_outcomes],
            "ordered_relation_record_hashes": list(record_hashes),
            "reason_codes": [reason.value for reason in reason_codes],
            "request_hash": request.request_hash,
            "status": status.value,
        }
        result = object.__new__(cls)
        object.__setattr__(result, "request_hash", request.request_hash)
        object.__setattr__(
            result,
            "evaluation_policy_version",
            request.evaluation_policy_version,
        )
        object.__setattr__(
            result,
            "ordered_hypothesis_ids",
            request.ordered_hypothesis_ids,
        )
        object.__setattr__(result, "ordered_relation_record_hashes", record_hashes)
        object.__setattr__(result, "ordered_outcomes", ordered_outcomes)
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "reason_codes", reason_codes)
        object.__setattr__(
            result,
            "evaluation_result_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(result, "result_hash", sha256_payload(canonical_payload))
        result._validate()
        return result

    def _validate(self) -> None:
        _sha256(self.request_hash, "request_hash")
        for hypothesis_id in self.ordered_hypothesis_ids:
            _sha256(hypothesis_id, "ordered_hypothesis_ids item")
        for record_hash in self.ordered_relation_record_hashes:
            _sha256(record_hash, "ordered_relation_record_hashes item")
        if len(self.ordered_outcomes) != len(self.ordered_hypothesis_ids):
            raise ValueError("ordered_outcomes must align with ordered_hypothesis_ids")
        if any(
            type(outcome) is not HypothesisEvaluationOutcome
            for outcome in self.ordered_outcomes
        ):
            raise TypeError(
                "ordered_outcomes must contain HypothesisEvaluationOutcome values"
            )
        if type(self.status) is not HypothesisEvaluationStatus:
            raise TypeError("status must be HypothesisEvaluationStatus")
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        if any(
            type(reason) is not HypothesisEvaluationReason
            for reason in self.reason_codes
        ):
            raise TypeError(
                "reason_codes must contain HypothesisEvaluationReason values"
            )
        if self.evaluation_result_contract_version != CONTRACT_VERSION:
            raise ValueError("evaluation_result_contract_version is invalid")
        _sha256(self.result_hash, "result_hash")
        if self.result_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("result_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which result_hash is derived."""
        return {
            "evaluation_policy_version": self.evaluation_policy_version,
            "evaluation_result_contract_version": (
                self.evaluation_result_contract_version
            ),
            "ordered_hypothesis_ids": list(self.ordered_hypothesis_ids),
            "ordered_outcomes": [outcome.value for outcome in self.ordered_outcomes],
            "ordered_relation_record_hashes": list(
                self.ordered_relation_record_hashes
            ),
            "reason_codes": [reason.value for reason in self.reason_codes],
            "request_hash": self.request_hash,
            "status": self.status.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical result payload with its content identity."""
        return {**self.canonical_payload(), "result_hash": self.result_hash}


def build_hypothesis_evaluation_result(
    request: HypothesisEvaluationRequest,
    *,
    relations: tuple[EvidenceHypothesisRelationRecord, ...],
    ordered_outcomes: tuple[HypothesisEvaluationOutcome, ...],
    status: HypothesisEvaluationStatus,
    reason_codes: tuple[HypothesisEvaluationReason, ...],
) -> HypothesisEvaluationResult:
    """Evaluate one exact L5.0 request into a structural L5.3 result."""
    if type(request) is not HypothesisEvaluationRequest:
        raise TypeError("request must be HypothesisEvaluationRequest")
    if any(
        type(record) is not EvidenceHypothesisRelationRecord
        for record in relations
    ):
        raise TypeError(
            "relations must contain EvidenceHypothesisRelationRecord values"
        )
    record_hashes = tuple(record.record_hash for record in relations)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("relations cannot contain duplicate record hashes")
    hypothesis_ids = frozenset(request.ordered_hypothesis_ids)
    supporting = frozenset(request.ordered_supporting_claim_hashes)
    contradicting = frozenset(request.ordered_contradicting_claim_hashes)
    for record in relations:
        if record.hypothesis_id not in hypothesis_ids:
            raise ValueError("relation hypothesis is outside the request")
        if (
            record.relation_type is EvidenceHypothesisRelationType.SUPPORTS
            and record.claim_hash not in supporting
        ):
            raise ValueError("support relation claim is outside the request")
        if (
            record.relation_type is EvidenceHypothesisRelationType.CONTRADICTS
            and record.claim_hash not in contradicting
        ):
            raise ValueError("contradict relation claim is outside the request")
    if len(ordered_outcomes) != len(request.ordered_hypothesis_ids):
        raise ValueError("ordered_outcomes must align with ordered_hypothesis_ids")
    if any(
        type(outcome) is not HypothesisEvaluationOutcome
        for outcome in ordered_outcomes
    ):
        raise TypeError(
            "ordered_outcomes must contain HypothesisEvaluationOutcome values"
        )
    if type(status) is not HypothesisEvaluationStatus:
        raise TypeError("status must be HypothesisEvaluationStatus")
    if any(
        type(reason) is not HypothesisEvaluationReason for reason in reason_codes
    ):
        raise TypeError("reason_codes must contain HypothesisEvaluationReason values")
    return HypothesisEvaluationResult._from_request(
        request,
        relations=relations,
        ordered_outcomes=ordered_outcomes,
        status=status,
        reason_codes=reason_codes,
    )
