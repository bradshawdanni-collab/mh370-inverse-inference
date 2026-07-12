"""Immutable deterministic L5.0 hypothesis evaluation input contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.reasoning.result import ConstrainedReasoningResult
from mh370_inverse_inference.reasoning.trace import NeutralReasoningTrace

CONTRACT_VERSION = "L5.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class HypothesisEvaluationRequest:
    """Content-addressed neutral evaluation input bound to exact L4 lineage."""

    reasoning_result_hash: str
    reasoning_trace_hash: str
    hypothesis_schema_version: str
    evaluation_policy_version: str
    ordered_hypothesis_ids: tuple[str, ...]
    ordered_supporting_claim_hashes: tuple[str, ...]
    ordered_contradicting_claim_hashes: tuple[str, ...]
    evaluation_contract_version: str
    request_hash: str

    @classmethod
    def _from_reasoning_lineage(
        cls,
        result: ConstrainedReasoningResult,
        trace: NeutralReasoningTrace,
        *,
        hypothesis_schema_version: str,
        evaluation_policy_version: str,
        ordered_hypothesis_ids: tuple[str, ...],
        ordered_supporting_claim_hashes: tuple[str, ...],
        ordered_contradicting_claim_hashes: tuple[str, ...],
        permitted_claim_hashes: frozenset[str],
    ) -> HypothesisEvaluationRequest:
        if trace.reasoning_result_hash != result.result_hash:
            raise ValueError("trace must reference the supplied reasoning result")
        _non_empty(hypothesis_schema_version, "hypothesis_schema_version")
        _non_empty(evaluation_policy_version, "evaluation_policy_version")
        if not ordered_hypothesis_ids:
            raise ValueError("ordered_hypothesis_ids cannot be empty")
        for hypothesis_id in ordered_hypothesis_ids:
            _non_empty(hypothesis_id, "ordered_hypothesis_ids item")
        if len(set(ordered_hypothesis_ids)) != len(ordered_hypothesis_ids):
            raise ValueError("ordered_hypothesis_ids cannot contain duplicates")

        supporting = ordered_supporting_claim_hashes
        contradicting = ordered_contradicting_claim_hashes
        for claim_hash in (*supporting, *contradicting):
            _sha256(claim_hash, "claim hash")
        if len(set(supporting)) != len(supporting):
            raise ValueError("supporting claim hashes cannot contain duplicates")
        if len(set(contradicting)) != len(contradicting):
            raise ValueError("contradicting claim hashes cannot contain duplicates")
        if set(supporting) & set(contradicting):
            raise ValueError("a claim cannot both support and contradict")
        missing = tuple(
            claim_hash
            for claim_hash in (*supporting, *contradicting)
            if claim_hash not in permitted_claim_hashes
        )
        if missing:
            raise ValueError("claim hashes contain values outside permitted lineage")

        canonical_payload: dict[str, Any] = {
            "evaluation_contract_version": CONTRACT_VERSION,
            "evaluation_policy_version": evaluation_policy_version,
            "hypothesis_schema_version": hypothesis_schema_version,
            "ordered_contradicting_claim_hashes": list(contradicting),
            "ordered_hypothesis_ids": list(ordered_hypothesis_ids),
            "ordered_supporting_claim_hashes": list(supporting),
            "reasoning_result_hash": result.result_hash,
            "reasoning_trace_hash": trace.trace_hash,
        }
        request = object.__new__(cls)
        object.__setattr__(request, "reasoning_result_hash", result.result_hash)
        object.__setattr__(request, "reasoning_trace_hash", trace.trace_hash)
        object.__setattr__(
            request,
            "hypothesis_schema_version",
            hypothesis_schema_version,
        )
        object.__setattr__(
            request,
            "evaluation_policy_version",
            evaluation_policy_version,
        )
        object.__setattr__(request, "ordered_hypothesis_ids", ordered_hypothesis_ids)
        object.__setattr__(
            request,
            "ordered_supporting_claim_hashes",
            supporting,
        )
        object.__setattr__(
            request,
            "ordered_contradicting_claim_hashes",
            contradicting,
        )
        object.__setattr__(request, "evaluation_contract_version", CONTRACT_VERSION)
        object.__setattr__(request, "request_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        _sha256(self.reasoning_result_hash, "reasoning_result_hash")
        _sha256(self.reasoning_trace_hash, "reasoning_trace_hash")
        if self.evaluation_contract_version != CONTRACT_VERSION:
            raise ValueError("evaluation_contract_version is invalid")
        _sha256(self.request_hash, "request_hash")
        if self.request_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("request_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which request_hash is derived."""
        return {
            "evaluation_contract_version": self.evaluation_contract_version,
            "evaluation_policy_version": self.evaluation_policy_version,
            "hypothesis_schema_version": self.hypothesis_schema_version,
            "ordered_contradicting_claim_hashes": list(
                self.ordered_contradicting_claim_hashes
            ),
            "ordered_hypothesis_ids": list(self.ordered_hypothesis_ids),
            "ordered_supporting_claim_hashes": list(
                self.ordered_supporting_claim_hashes
            ),
            "reasoning_result_hash": self.reasoning_result_hash,
            "reasoning_trace_hash": self.reasoning_trace_hash,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "request_hash": self.request_hash}


def build_hypothesis_evaluation_request(
    result: ConstrainedReasoningResult,
    trace: NeutralReasoningTrace,
    *,
    hypothesis_schema_version: str,
    evaluation_policy_version: str,
    ordered_hypothesis_ids: tuple[str, ...],
    ordered_supporting_claim_hashes: tuple[str, ...],
    ordered_contradicting_claim_hashes: tuple[str, ...],
    permitted_claim_hashes: frozenset[str],
) -> HypothesisEvaluationRequest:
    """Bind exact L4 lineage to a neutral deterministic L5.0 input."""
    if type(result) is not ConstrainedReasoningResult:
        raise TypeError("result must be ConstrainedReasoningResult")
    if type(trace) is not NeutralReasoningTrace:
        raise TypeError("trace must be NeutralReasoningTrace")
    if type(permitted_claim_hashes) is not frozenset:
        raise TypeError("permitted_claim_hashes must be frozenset")
    return HypothesisEvaluationRequest._from_reasoning_lineage(
        result,
        trace,
        hypothesis_schema_version=hypothesis_schema_version,
        evaluation_policy_version=evaluation_policy_version,
        ordered_hypothesis_ids=ordered_hypothesis_ids,
        ordered_supporting_claim_hashes=ordered_supporting_claim_hashes,
        ordered_contradicting_claim_hashes=ordered_contradicting_claim_hashes,
        permitted_claim_hashes=permitted_claim_hashes,
    )
