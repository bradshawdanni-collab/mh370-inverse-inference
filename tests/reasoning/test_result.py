"""Tests for the deterministic L4.1 constrained reasoning result contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation import (
    InterpretationReason,
    InterpretationStatus,
    build_interpretation_request,
    build_interpretation_result,
)
from mh370_inverse_inference.reasoning import (
    ConstrainedReasoningRequest,
    ConstrainedReasoningResult,
    ReasoningReason,
    ReasoningStatus,
    build_constrained_reasoning_request,
    build_constrained_reasoning_result,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _request() -> ConstrainedReasoningRequest:
    projection = AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )
    interpretation_request = build_interpretation_request(projection)
    interpretation_result = build_interpretation_result(
        interpretation_request,
        interpretation_policy_version="interpretation-1.0.0",
        status=InterpretationStatus.ACCEPTED,
        reason_codes=(InterpretationReason.OK,),
        derived_claims=(),
    )
    return build_constrained_reasoning_request(
        interpretation_result,
        reasoning_policy_version="reasoning-1.0.0",
    )


def _result(
    status: ReasoningStatus = ReasoningStatus.ACCEPTED,
    reason_codes: tuple[ReasoningReason, ...] = (ReasoningReason.OK,),
) -> ConstrainedReasoningResult:
    return build_constrained_reasoning_result(
        _request(),
        status=status,
        reason_codes=reason_codes,
    )


def test_result_is_deterministic_and_content_addressed() -> None:
    first = _result()
    second = _result()

    assert first == second
    assert first.request_hash == _request().request_hash
    assert first.reasoning_policy_version == "reasoning-1.0.0"
    assert first.reasoning_contract_version == "L4.1"
    assert first.reasoning_outputs == ()
    assert first.result_hash == sha256_payload(first.canonical_payload())


def test_result_supports_all_neutral_statuses() -> None:
    cases = (
        (ReasoningStatus.ACCEPTED, ReasoningReason.OK),
        (ReasoningStatus.REJECTED, ReasoningReason.POLICY_REJECTED),
        (
            ReasoningStatus.INSUFFICIENT_BASIS,
            ReasoningReason.INSUFFICIENT_BASIS,
        ),
        (
            ReasoningStatus.CONSTRAINT_VIOLATION,
            ReasoningReason.CONSTRAINT_VIOLATION,
        ),
    )

    for status, reason in cases:
        result = _result(status, (reason,))
        assert result.status is status
        assert result.reason_codes == (reason,)


def test_reason_order_is_part_of_result_identity() -> None:
    first = _result(
        ReasoningStatus.REJECTED,
        (
            ReasoningReason.POLICY_REJECTED,
            ReasoningReason.INSUFFICIENT_BASIS,
        ),
    )
    second = _result(
        ReasoningStatus.REJECTED,
        (
            ReasoningReason.INSUFFICIENT_BASIS,
            ReasoningReason.POLICY_REJECTED,
        ),
    )

    assert first.result_hash != second.result_hash


def test_result_is_frozen() -> None:
    result = _result()

    with pytest.raises(FrozenInstanceError):
        result.result_hash = HASH_A  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    result_type: Any = ConstrainedReasoningResult
    builder: Any = build_constrained_reasoning_result

    with pytest.raises(TypeError):
        result_type(
            request_hash=HASH_A,
            reasoning_contract_version="L4.1",
            reasoning_policy_version="reasoning-1.0.0",
            status=ReasoningStatus.ACCEPTED,
            reason_codes=(ReasoningReason.OK,),
            reasoning_outputs=(),
            result_hash=HASH_B,
        )

    for value in ({"request_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(
                value,
                status=ReasoningStatus.ACCEPTED,
                reason_codes=(ReasoningReason.OK,),
            )


def test_empty_reason_codes_are_rejected() -> None:
    with pytest.raises(ValueError, match="reason_codes cannot be empty"):
        build_constrained_reasoning_result(
            _request(),
            status=ReasoningStatus.REJECTED,
            reason_codes=(),
        )


def test_result_payload_contains_only_neutral_contract_fields() -> None:
    result = _result()

    assert set(result.to_payload()) == {
        "reason_codes",
        "reasoning_contract_version",
        "reasoning_outputs",
        "reasoning_policy_version",
        "request_hash",
        "result_hash",
        "status",
    }


def test_result_module_excludes_authority_and_inference_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/reasoning/result.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "registration_models",
        "registeredevidencerecord",
        "raw_evidence",
        "datetime",
        "uuid",
        "random",
        "requests",
        "socket",
        "likelihood",
        "probability",
        "confidence",
        "bayesian",
        "trajectory",
        "drift",
        "endpoint",
        "coordinate",
        "location",
        "filesystem",
        "pathlib",
    )

    for token in forbidden:
        assert token not in source
