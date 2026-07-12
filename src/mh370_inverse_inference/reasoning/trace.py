"""Immutable deterministic L4.3 neutral reasoning trace contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.reasoning.application import RuleApplicationRecord
from mh370_inverse_inference.reasoning.result import ConstrainedReasoningResult

CONTRACT_VERSION = "L4.3"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class NeutralReasoningTrace:
    """Content-addressed ordered trace over one exact L4.1 result."""

    reasoning_result_hash: str
    ordered_rule_application_hashes: tuple[str, ...]
    trace_contract_version: str
    trace_hash: str

    @classmethod
    def _from_reasoning_result(
        cls,
        result: ConstrainedReasoningResult,
        *,
        records: tuple[RuleApplicationRecord, ...],
    ) -> NeutralReasoningTrace:
        ordered_hashes = tuple(record.record_hash for record in records)
        canonical_payload: dict[str, Any] = {
            "ordered_rule_application_hashes": list(ordered_hashes),
            "reasoning_result_hash": result.result_hash,
            "trace_contract_version": CONTRACT_VERSION,
        }
        trace = object.__new__(cls)
        object.__setattr__(trace, "reasoning_result_hash", result.result_hash)
        object.__setattr__(
            trace,
            "ordered_rule_application_hashes",
            ordered_hashes,
        )
        object.__setattr__(trace, "trace_contract_version", CONTRACT_VERSION)
        object.__setattr__(trace, "trace_hash", sha256_payload(canonical_payload))
        trace._validate()
        return trace

    def _validate(self) -> None:
        _sha256(self.reasoning_result_hash, "reasoning_result_hash")
        for record_hash in self.ordered_rule_application_hashes:
            _sha256(record_hash, "ordered_rule_application_hashes item")
        if len(set(self.ordered_rule_application_hashes)) != len(
            self.ordered_rule_application_hashes
        ):
            raise ValueError("ordered_rule_application_hashes cannot contain duplicates")
        if self.trace_contract_version != CONTRACT_VERSION:
            raise ValueError("trace_contract_version is invalid")
        _sha256(self.trace_hash, "trace_hash")
        if self.trace_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("trace_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which trace_hash is derived."""
        return {
            "ordered_rule_application_hashes": list(
                self.ordered_rule_application_hashes
            ),
            "reasoning_result_hash": self.reasoning_result_hash,
            "trace_contract_version": self.trace_contract_version,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical trace payload with its content identity."""
        return {**self.canonical_payload(), "trace_hash": self.trace_hash}


def build_neutral_reasoning_trace(
    result: ConstrainedReasoningResult,
    *,
    records: tuple[RuleApplicationRecord, ...],
) -> NeutralReasoningTrace:
    """Bind one L4.1 result to ordered L4.2 record identities."""
    if type(result) is not ConstrainedReasoningResult:
        raise TypeError("result must be ConstrainedReasoningResult")
    if any(type(record) is not RuleApplicationRecord for record in records):
        raise TypeError("records must contain RuleApplicationRecord values")
    if any(record.reasoning_result_hash != result.result_hash for record in records):
        raise ValueError("records must reference the supplied reasoning result")
    record_hashes = tuple(record.record_hash for record in records)
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    return NeutralReasoningTrace._from_reasoning_result(result, records=records)
