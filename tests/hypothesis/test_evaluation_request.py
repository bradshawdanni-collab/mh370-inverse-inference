"""Tests for the deterministic L5.0 hypothesis evaluation input contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    HypothesisEvaluationRequest,
    build_hypothesis_evaluation_request,
)
from mh370_inverse_inference.interpretation import (
    InterpretationReason,
    InterpretationStatus,
    build_interpretation_request,
    build_interpretation_result,
)
from mh370_inverse_inference.reasoning import (
    ConstrainedReasoningResult,
    NeutralReasoningTrace,
    ReasoningReason,
    ReasoningStatus,
    build_constrained_reasoning_request,
    build_constrained_reasoning_result,
    build_neutral_reasoning_trace,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _reasoning_lineage(
    *,
    policy_version: str = "reasoning-1.0.0",
) -> tuple[ConstrainedReasoningResult, NeutralReasoningTrace]:
    projection = AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )
    interpretation_input = build_interpretation_request(projection)
    interpretation_result = build_interpretation_result(
        interpretation_input,
        interpretation_policy_version="interpretation-1.0.0",
        status=InterpretationStatus.ACCEPTED,
        reason_codes=(InterpretationReason.OK,),
        derived_claims=(),
    )
    reasoning_input = build_constrained_reasoning_request(
        interpretation_result,
        reasoning_policy_version=policy_version,
    )
    reasoning_result = build_constrained_reasoning_result(
        reasoning_input,
        status=ReasoningStatus.ACCEPTED,
        reason_codes=(ReasoningReason.OK,),
    )
    trace = build_neutral_reasoning_trace(reasoning_result, records=())
    return reasoning_result, trace


def _request(
    *,
    ordered_hypothesis_ids: tuple[str, ...] = ("HYP-001", "HYP-002"),
    ordered_supporting_claim_hashes: tuple[str, ...] = (HASH_A,),
    ordered_contradicting_claim_hashes: tuple[str, ...] = (HASH_B,),
) -> HypothesisEvaluationRequest:
    result, trace = _reasoning_lineage()
    return build_hypothesis_evaluation_request(
        result,
        trace,
        hypothesis_schema_version="hypothesis-schema-1.0.0",
        evaluation_policy_version="evaluation-1.0.0",
        ordered_hypothesis_ids=ordered_hypothesis_ids,
        ordered_supporting_claim_hashes=ordered_supporting_claim_hashes,
        ordered_contradicting_claim_hashes=ordered_contradicting_claim_hashes,
        permitted_claim_hashes=frozenset((HASH_A, HASH_B, HASH_C)),
    )


def test_request_is_deterministic_and_content_addressed() -> None:
    first = _request()
    second = _request()
    result, trace = _reasoning_lineage()

    assert first == second
    assert first.reasoning_result_hash == result.result_hash
    assert first.reasoning_trace_hash == trace.trace_hash
    assert first.evaluation_contract_version == "L5.0"
    assert first.request_hash == sha256_payload(first.canonical_payload())


def test_order_is_part_of_request_identity() -> None:
    hypothesis_first = _request(ordered_hypothesis_ids=("HYP-001", "HYP-002"))
    hypothesis_second = _request(ordered_hypothesis_ids=("HYP-002", "HYP-001"))
    support_first = _request(ordered_supporting_claim_hashes=(HASH_A, HASH_C))
    support_second = _request(ordered_supporting_claim_hashes=(HASH_C, HASH_A))

    assert hypothesis_first.request_hash != hypothesis_second.request_hash
    assert support_first.request_hash != support_second.request_hash


def test_mismatched_result_and_trace_are_rejected() -> None:
    result, _ = _reasoning_lineage(policy_version="reasoning-1.0.0")
    _, trace = _reasoning_lineage(policy_version="reasoning-2.0.0")

    with pytest.raises(ValueError, match="trace must reference"):
        build_hypothesis_evaluation_request(
            result,
            trace,
            hypothesis_schema_version="hypothesis-schema-1.0.0",
            evaluation_policy_version="evaluation-1.0.0",
            ordered_hypothesis_ids=("HYP-001",),
            ordered_supporting_claim_hashes=(),
            ordered_contradicting_claim_hashes=(),
            permitted_claim_hashes=frozenset(),
        )


def test_duplicate_overlap_and_unpermitted_claims_are_rejected() -> None:
    with pytest.raises(ValueError, match="ordered_hypothesis_ids"):
        _request(ordered_hypothesis_ids=("HYP-001", "HYP-001"))
    with pytest.raises(ValueError, match="supporting claim hashes"):
        _request(ordered_supporting_claim_hashes=(HASH_A, HASH_A))
    with pytest.raises(ValueError, match="both support and contradict"):
        _request(
            ordered_supporting_claim_hashes=(HASH_A,),
            ordered_contradicting_claim_hashes=(HASH_A,),
        )

    result, trace = _reasoning_lineage()
    with pytest.raises(ValueError, match="outside permitted lineage"):
        build_hypothesis_evaluation_request(
            result,
            trace,
            hypothesis_schema_version="hypothesis-schema-1.0.0",
            evaluation_policy_version="evaluation-1.0.0",
            ordered_hypothesis_ids=("HYP-001",),
            ordered_supporting_claim_hashes=(HASH_C,),
            ordered_contradicting_claim_hashes=(),
            permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
        )


def test_request_is_frozen() -> None:
    request = _request()

    with pytest.raises(FrozenInstanceError):
        request.request_hash = HASH_C  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    request_type: Any = HypothesisEvaluationRequest
    builder: Any = build_hypothesis_evaluation_request

    with pytest.raises(TypeError):
        request_type(
            reasoning_result_hash=HASH_A,
            reasoning_trace_hash=HASH_B,
            hypothesis_schema_version="hypothesis-schema-1.0.0",
            evaluation_policy_version="evaluation-1.0.0",
            ordered_hypothesis_ids=("HYP-001",),
            ordered_supporting_claim_hashes=(),
            ordered_contradicting_claim_hashes=(),
            evaluation_contract_version="L5.0",
            request_hash=HASH_C,
        )

    _, trace = _reasoning_lineage()
    for value in ({"result_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(
                value,
                trace,
                hypothesis_schema_version="hypothesis-schema-1.0.0",
                evaluation_policy_version="evaluation-1.0.0",
                ordered_hypothesis_ids=("HYP-001",),
                ordered_supporting_claim_hashes=(),
                ordered_contradicting_claim_hashes=(),
                permitted_claim_hashes=frozenset(),
            )


def test_request_payload_contains_only_contract_fields() -> None:
    request = _request()

    assert set(request.to_payload()) == {
        "evaluation_contract_version",
        "evaluation_policy_version",
        "hypothesis_schema_version",
        "ordered_contradicting_claim_hashes",
        "ordered_hypothesis_ids",
        "ordered_supporting_claim_hashes",
        "reasoning_result_hash",
        "reasoning_trace_hash",
        "request_hash",
    }


def test_request_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/hypothesis/request.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "registration_models",
        "registeredevidencerecord",
        "raw_evidence",
        "datetime",
        "uuid",
        "random",
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
        "database",
    )

    for token in forbidden:
        assert token not in source
