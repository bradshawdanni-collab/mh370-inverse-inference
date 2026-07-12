"""One-way projection from an L3 interpretation result into an L4 input."""

from __future__ import annotations

from mh370_inverse_inference.interpretation.result import InterpretationResult
from mh370_inverse_inference.reasoning.models import ConstrainedReasoningRequest


def build_constrained_reasoning_request(
    result: InterpretationResult,
    *,
    reasoning_policy_version: str,
) -> ConstrainedReasoningRequest:
    """Build an L4.0 request from one exact L3 interpretation result."""
    if type(result) is not InterpretationResult:
        raise TypeError("result must be InterpretationResult")
    if not reasoning_policy_version.strip():
        raise ValueError("reasoning_policy_version cannot be blank")
    return ConstrainedReasoningRequest._from_interpretation_result(
        result,
        reasoning_policy_version=reasoning_policy_version,
    )
