"""Immutable deterministic L7.0 admissibility decision request contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.comparative.result import ComparativeAssessmentResult
from mh370_inverse_inference.comparative.trace import ComparativeAssessmentTrace
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L7.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class AdmissibilityDecisionRequest:
    """Content-addressed synthesis input over exact ordered L6 lineage."""

    ordered_comparative_result_hashes: tuple[str, ...]
    ordered_comparative_trace_hashes: tuple[str, ...]
    admissibility_policy_version: str
    admissibility_request_contract_version: str
    request_hash: str

    @classmethod
    def _from_l6_lineage(
        cls,
        results: tuple[ComparativeAssessmentResult, ...],
        traces: tuple[ComparativeAssessmentTrace, ...],
        *,
        admissibility_policy_version: str,
    ) -> AdmissibilityDecisionRequest:
        result_hashes = tuple(result.result_hash for result in results)
        trace_hashes = tuple(trace.trace_hash for trace in traces)
        canonical_payload: dict[str, Any] = {
            "admissibility_policy_version": admissibility_policy_version,
            "admissibility_request_contract_version": CONTRACT_VERSION,
            "ordered_comparative_result_hashes": list(result_hashes),
            "ordered_comparative_trace_hashes": list(trace_hashes),
        }
        request = object.__new__(cls)
        object.__setattr__(
            request,
            "ordered_comparative_result_hashes",
            result_hashes,
        )
        object.__setattr__(
            request,
            "ordered_comparative_trace_hashes",
            trace_hashes,
        )
        object.__setattr__(
            request,
            "admissibility_policy_version",
            admissibility_policy_version,
        )
        object.__setattr__(
            request,
            "admissibility_request_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(request, "request_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        if not self.ordered_comparative_result_hashes:
            raise ValueError("at least one comparative result is required")
        for result_hash in self.ordered_comparative_result_hashes:
            _sha256(result_hash, "ordered_comparative_result_hashes item")
        for trace_hash in self.ordered_comparative_trace_hashes:
            _sha256(trace_hash, "ordered_comparative_trace_hashes item")
        if len(self.ordered_comparative_result_hashes) != len(
            self.ordered_comparative_trace_hashes
        ):
            raise ValueError("each comparative result must have one comparative trace")
        if len(set(self.ordered_comparative_result_hashes)) != len(
            self.ordered_comparative_result_hashes
        ):
            raise ValueError("comparative result hashes cannot contain duplicates")
        if len(set(self.ordered_comparative_trace_hashes)) != len(
            self.ordered_comparative_trace_hashes
        ):
            raise ValueError("comparative trace hashes cannot contain duplicates")
        _non_empty(self.admissibility_policy_version, "admissibility_policy_version")
        if self.admissibility_request_contract_version != CONTRACT_VERSION:
            raise ValueError("admissibility_request_contract_version is invalid")
        _sha256(self.request_hash, "request_hash")
        if self.request_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("request_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which request_hash is derived."""
        return {
            "admissibility_policy_version": self.admissibility_policy_version,
            "admissibility_request_contract_version": (
                self.admissibility_request_contract_version
            ),
            "ordered_comparative_result_hashes": list(
                self.ordered_comparative_result_hashes
            ),
            "ordered_comparative_trace_hashes": list(
                self.ordered_comparative_trace_hashes
            ),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "request_hash": self.request_hash}


def build_admissibility_decision_request(
    results: tuple[ComparativeAssessmentResult, ...],
    traces: tuple[ComparativeAssessmentTrace, ...],
    *,
    admissibility_policy_version: str,
) -> AdmissibilityDecisionRequest:
    """Bind exact ordered L6 result and trace lineage into one L7.0 request."""
    if any(type(result) is not ComparativeAssessmentResult for result in results):
        raise TypeError("results must contain ComparativeAssessmentResult values")
    if any(type(trace) is not ComparativeAssessmentTrace for trace in traces):
        raise TypeError("traces must contain ComparativeAssessmentTrace values")
    if not results:
        raise ValueError("at least one comparative result is required")
    if len(results) != len(traces):
        raise ValueError("each comparative result must have one comparative trace")
    result_hashes = tuple(result.result_hash for result in results)
    trace_hashes = tuple(trace.trace_hash for trace in traces)
    if len(set(result_hashes)) != len(result_hashes):
        raise ValueError("results cannot contain duplicate result hashes")
    if len(set(trace_hashes)) != len(trace_hashes):
        raise ValueError("traces cannot contain duplicate trace hashes")
    if any(
        trace.comparative_result_hash != result.result_hash
        for result, trace in zip(results, traces, strict=True)
    ):
        raise ValueError("each trace must reference its paired comparative result")
    if any(
        trace.comparative_request_hash != result.comparative_request_hash
        for result, trace in zip(results, traces, strict=True)
    ):
        raise ValueError("each trace must preserve paired comparative request lineage")
    _non_empty(admissibility_policy_version, "admissibility_policy_version")
    return AdmissibilityDecisionRequest._from_l6_lineage(
        results,
        traces,
        admissibility_policy_version=admissibility_policy_version,
    )
