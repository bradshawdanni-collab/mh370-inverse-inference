"""Immutable deterministic L7.1 admissibility decision record contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.admissibility.request import AdmissibilityDecisionRequest
from mh370_inverse_inference.comparative.result import ComparativeAssessmentResult
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L7.1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AdmissibilityOutcome(StrEnum):
    """Rule-bound structural disposition for one admitted comparative result."""

    ADMISSIBLE = "ADMISSIBLE"
    INADMISSIBLE = "INADMISSIBLE"
    INDETERMINATE = "INDETERMINATE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class AdmissibilityDecisionRecord:
    """Content-addressed admissibility decision for one admitted L6 result."""

    admissibility_request_hash: str
    comparative_result_hash: str
    outcome: AdmissibilityOutcome
    decision_rule_id: str
    decision_rule_version: str
    admissibility_record_contract_version: str
    record_hash: str

    @classmethod
    def _from_request(
        cls,
        request: AdmissibilityDecisionRequest,
        result: ComparativeAssessmentResult,
        *,
        outcome: AdmissibilityOutcome,
        decision_rule_id: str,
        decision_rule_version: str,
    ) -> AdmissibilityDecisionRecord:
        canonical_payload: dict[str, Any] = {
            "admissibility_record_contract_version": CONTRACT_VERSION,
            "admissibility_request_hash": request.request_hash,
            "comparative_result_hash": result.result_hash,
            "decision_rule_id": decision_rule_id,
            "decision_rule_version": decision_rule_version,
            "outcome": outcome.value,
        }
        record = object.__new__(cls)
        object.__setattr__(
            record,
            "admissibility_request_hash",
            request.request_hash,
        )
        object.__setattr__(record, "comparative_result_hash", result.result_hash)
        object.__setattr__(record, "outcome", outcome)
        object.__setattr__(record, "decision_rule_id", decision_rule_id)
        object.__setattr__(record, "decision_rule_version", decision_rule_version)
        object.__setattr__(
            record,
            "admissibility_record_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(record, "record_hash", sha256_payload(canonical_payload))
        record._validate()
        return record

    def _validate(self) -> None:
        _sha256(self.admissibility_request_hash, "admissibility_request_hash")
        _sha256(self.comparative_result_hash, "comparative_result_hash")
        if type(self.outcome) is not AdmissibilityOutcome:
            raise TypeError("outcome must be AdmissibilityOutcome")
        _non_empty(self.decision_rule_id, "decision_rule_id")
        _non_empty(self.decision_rule_version, "decision_rule_version")
        if self.admissibility_record_contract_version != CONTRACT_VERSION:
            raise ValueError("admissibility_record_contract_version is invalid")
        _sha256(self.record_hash, "record_hash")
        if self.record_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("record_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which record_hash is derived."""
        return {
            "admissibility_record_contract_version": (
                self.admissibility_record_contract_version
            ),
            "admissibility_request_hash": self.admissibility_request_hash,
            "comparative_result_hash": self.comparative_result_hash,
            "decision_rule_id": self.decision_rule_id,
            "decision_rule_version": self.decision_rule_version,
            "outcome": self.outcome.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical record payload with its content identity."""
        return {**self.canonical_payload(), "record_hash": self.record_hash}


def build_admissibility_decision_record(
    request: AdmissibilityDecisionRequest,
    result: ComparativeAssessmentResult,
    *,
    outcome: AdmissibilityOutcome,
    decision_rule_id: str,
    decision_rule_version: str,
) -> AdmissibilityDecisionRecord:
    """Bind one admitted L6 result to an explicit deterministic L7.1 decision."""
    if type(request) is not AdmissibilityDecisionRequest:
        raise TypeError("request must be AdmissibilityDecisionRequest")
    if type(result) is not ComparativeAssessmentResult:
        raise TypeError("result must be ComparativeAssessmentResult")
    if result.result_hash not in request.ordered_comparative_result_hashes:
        raise ValueError("result is outside the supplied admissibility request")
    if type(outcome) is not AdmissibilityOutcome:
        raise TypeError("outcome must be AdmissibilityOutcome")
    _non_empty(decision_rule_id, "decision_rule_id")
    _non_empty(decision_rule_version, "decision_rule_version")
    return AdmissibilityDecisionRecord._from_request(
        request,
        result,
        outcome=outcome,
        decision_rule_id=decision_rule_id,
        decision_rule_version=decision_rule_version,
    )
