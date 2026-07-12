"""Immutable deterministic L4.2 rule application record contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.reasoning.result import ConstrainedReasoningResult

CONTRACT_VERSION = "L4.2"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class RuleApplicationOutcome(StrEnum):
    """Stable neutral outcomes for one rule application."""

    APPLIED = "APPLIED"
    NOT_APPLIED = "NOT_APPLIED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_BLOCKED = "CONSTRAINT_BLOCKED"


class RuleApplicationReason(StrEnum):
    """Stable machine-readable reasons for one rule application."""

    OK = "OK"
    RULE_NOT_SATISFIED = "RULE_NOT_SATISFIED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_BLOCKED = "CONSTRAINT_BLOCKED"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class RuleApplicationRecord:
    """Content-addressed neutral record derived from one L4.1 result."""

    reasoning_result_hash: str
    rule_id: str
    rule_version: str
    input_claim_hashes: tuple[str, ...]
    outcome: RuleApplicationOutcome
    reason_codes: tuple[RuleApplicationReason, ...]
    rule_application_contract_version: str
    record_hash: str

    @classmethod
    def _from_reasoning_result(
        cls,
        result: ConstrainedReasoningResult,
        *,
        rule_id: str,
        rule_version: str,
        input_claim_hashes: tuple[str, ...],
        permitted_claim_hashes: frozenset[str],
        outcome: RuleApplicationOutcome,
        reason_codes: tuple[RuleApplicationReason, ...],
    ) -> RuleApplicationRecord:
        missing = tuple(
            claim_hash
            for claim_hash in input_claim_hashes
            if claim_hash not in permitted_claim_hashes
        )
        if missing:
            raise ValueError("input_claim_hashes contain values outside permitted lineage")

        canonical_payload: dict[str, Any] = {
            "input_claim_hashes": list(input_claim_hashes),
            "outcome": outcome.value,
            "reason_codes": [reason.value for reason in reason_codes],
            "reasoning_result_hash": result.result_hash,
            "rule_application_contract_version": CONTRACT_VERSION,
            "rule_id": rule_id,
            "rule_version": rule_version,
        }
        record = object.__new__(cls)
        object.__setattr__(record, "reasoning_result_hash", result.result_hash)
        object.__setattr__(record, "rule_id", rule_id)
        object.__setattr__(record, "rule_version", rule_version)
        object.__setattr__(record, "input_claim_hashes", input_claim_hashes)
        object.__setattr__(record, "outcome", outcome)
        object.__setattr__(record, "reason_codes", reason_codes)
        object.__setattr__(
            record,
            "rule_application_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(record, "record_hash", sha256_payload(canonical_payload))
        record._validate()
        return record

    def _validate(self) -> None:
        _sha256(self.reasoning_result_hash, "reasoning_result_hash")
        _non_empty(self.rule_id, "rule_id")
        _non_empty(self.rule_version, "rule_version")
        for claim_hash in self.input_claim_hashes:
            _sha256(claim_hash, "input_claim_hashes item")
        if type(self.outcome) is not RuleApplicationOutcome:
            raise TypeError("outcome must be RuleApplicationOutcome")
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        if any(
            type(reason) is not RuleApplicationReason for reason in self.reason_codes
        ):
            raise TypeError("reason_codes must contain RuleApplicationReason values")
        if self.rule_application_contract_version != CONTRACT_VERSION:
            raise ValueError(
                "rule_application_contract_version must be " f"{CONTRACT_VERSION}"
            )
        _sha256(self.record_hash, "record_hash")
        if self.record_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("record_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which record_hash is derived."""
        return {
            "input_claim_hashes": list(self.input_claim_hashes),
            "outcome": self.outcome.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "reasoning_result_hash": self.reasoning_result_hash,
            "rule_application_contract_version": (
                self.rule_application_contract_version
            ),
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical record payload with its content identity."""
        return {**self.canonical_payload(), "record_hash": self.record_hash}


def build_rule_application_record(
    result: ConstrainedReasoningResult,
    *,
    rule_id: str,
    rule_version: str,
    input_claim_hashes: tuple[str, ...],
    permitted_claim_hashes: frozenset[str],
    outcome: RuleApplicationOutcome,
    reason_codes: tuple[RuleApplicationReason, ...],
) -> RuleApplicationRecord:
    """Seal one L4.1 result into a neutral deterministic L4.2 record."""
    if type(result) is not ConstrainedReasoningResult:
        raise TypeError("result must be ConstrainedReasoningResult")
    if type(outcome) is not RuleApplicationOutcome:
        raise TypeError("outcome must be RuleApplicationOutcome")
    if any(type(reason) is not RuleApplicationReason for reason in reason_codes):
        raise TypeError("reason_codes must contain RuleApplicationReason values")
    if type(permitted_claim_hashes) is not frozenset:
        raise TypeError("permitted_claim_hashes must be frozenset")
    return RuleApplicationRecord._from_reasoning_result(
        result,
        rule_id=rule_id,
        rule_version=rule_version,
        input_claim_hashes=input_claim_hashes,
        permitted_claim_hashes=permitted_claim_hashes,
        outcome=outcome,
        reason_codes=reason_codes,
    )
