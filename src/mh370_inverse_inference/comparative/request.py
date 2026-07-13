"""Immutable deterministic L6.0 comparative assessment request contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis.result import HypothesisEvaluationResult
from mh370_inverse_inference.hypothesis.trace import HypothesisEvaluationTrace

CONTRACT_VERSION = "L6.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ComparativeAssessmentRequest:
    """Content-addressed comparison input over exact ordered L5 lineage."""

    ordered_evaluation_result_hashes: tuple[str, ...]
    ordered_evaluation_trace_hashes: tuple[str, ...]
    comparison_policy_version: str
    comparative_contract_version: str
    request_hash: str

    @classmethod
    def _from_l5_lineage(
        cls,
        results: tuple[HypothesisEvaluationResult, ...],
        traces: tuple[HypothesisEvaluationTrace, ...],
        *,
        comparison_policy_version: str,
    ) -> ComparativeAssessmentRequest:
        result_hashes = tuple(result.result_hash for result in results)
        trace_hashes = tuple(trace.trace_hash for trace in traces)
        canonical_payload: dict[str, Any] = {
            "comparison_policy_version": comparison_policy_version,
            "comparative_contract_version": CONTRACT_VERSION,
            "ordered_evaluation_result_hashes": list(result_hashes),
            "ordered_evaluation_trace_hashes": list(trace_hashes),
        }
        request = object.__new__(cls)
        object.__setattr__(
            request,
            "ordered_evaluation_result_hashes",
            result_hashes,
        )
        object.__setattr__(
            request,
            "ordered_evaluation_trace_hashes",
            trace_hashes,
        )
        object.__setattr__(
            request,
            "comparison_policy_version",
            comparison_policy_version,
        )
        object.__setattr__(
            request,
            "comparative_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(request, "request_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        if len(self.ordered_evaluation_result_hashes) < 2:
            raise ValueError("at least two evaluation results are required")
        for result_hash in self.ordered_evaluation_result_hashes:
            _sha256(result_hash, "ordered_evaluation_result_hashes item")
        for trace_hash in self.ordered_evaluation_trace_hashes:
            _sha256(trace_hash, "ordered_evaluation_trace_hashes item")
        if len(self.ordered_evaluation_result_hashes) != len(
            self.ordered_evaluation_trace_hashes
        ):
            raise ValueError("each evaluation result must have one evaluation trace")
        if len(set(self.ordered_evaluation_result_hashes)) != len(
            self.ordered_evaluation_result_hashes
        ):
            raise ValueError("evaluation result hashes cannot contain duplicates")
        if len(set(self.ordered_evaluation_trace_hashes)) != len(
            self.ordered_evaluation_trace_hashes
        ):
            raise ValueError("evaluation trace hashes cannot contain duplicates")
        _non_empty(self.comparison_policy_version, "comparison_policy_version")
        if self.comparative_contract_version != CONTRACT_VERSION:
            raise ValueError("comparative_contract_version is invalid")
        _sha256(self.request_hash, "request_hash")
        if self.request_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("request_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which request_hash is derived."""
        return {
            "comparison_policy_version": self.comparison_policy_version,
            "comparative_contract_version": self.comparative_contract_version,
            "ordered_evaluation_result_hashes": list(
                self.ordered_evaluation_result_hashes
            ),
            "ordered_evaluation_trace_hashes": list(
                self.ordered_evaluation_trace_hashes
            ),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "request_hash": self.request_hash}


def build_comparative_assessment_request(
    results: tuple[HypothesisEvaluationResult, ...],
    traces: tuple[HypothesisEvaluationTrace, ...],
    *,
    comparison_policy_version: str,
) -> ComparativeAssessmentRequest:
    """Bind exact ordered L5 result and trace lineage into one L6.0 request."""
    if any(type(result) is not HypothesisEvaluationResult for result in results):
        raise TypeError("results must contain HypothesisEvaluationResult values")
    if any(type(trace) is not HypothesisEvaluationTrace for trace in traces):
        raise TypeError("traces must contain HypothesisEvaluationTrace values")
    if len(results) < 2:
        raise ValueError("at least two evaluation results are required")
    if len(results) != len(traces):
        raise ValueError("each evaluation result must have one evaluation trace")
    result_hashes = tuple(result.result_hash for result in results)
    trace_hashes = tuple(trace.trace_hash for trace in traces)
    if len(set(result_hashes)) != len(result_hashes):
        raise ValueError("results cannot contain duplicate result hashes")
    if len(set(trace_hashes)) != len(trace_hashes):
        raise ValueError("traces cannot contain duplicate trace hashes")
    if any(
        trace.evaluation_result_hash != result.result_hash
        for result, trace in zip(results, traces, strict=True)
    ):
        raise ValueError("each trace must reference its paired evaluation result")
    hypothesis_ids = {
        hypothesis_id
        for result in results
        for hypothesis_id in result.ordered_hypothesis_ids
    }
    if len(hypothesis_ids) < 2:
        raise ValueError("at least two distinct hypotheses are required")
    _non_empty(comparison_policy_version, "comparison_policy_version")
    return ComparativeAssessmentRequest._from_l5_lineage(
        results,
        traces,
        comparison_policy_version=comparison_policy_version,
    )
