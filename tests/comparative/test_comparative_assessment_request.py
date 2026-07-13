"""Tests for the deterministic L6.0 comparative assessment request."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.comparative import (
    ComparativeAssessmentRequest,
    build_comparative_assessment_request,
)
from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    EvidenceHypothesisRelationType,
    HypothesisEvaluationOutcome,
    HypothesisEvaluationReason,
    HypothesisEvaluationStatus,
    HypothesisType,
    build_evidence_hypothesis_relation_record,
    build_hypothesis_definition,
    build_hypothesis_evaluation_request,
    build_hypothesis_evaluation_result,
    build_hypothesis_evaluation_trace,
)
from mh370_inverse_inference.interpretation import (
    InterpretationReason,
    InterpretationStatus,
    build_interpretation_request,
    build_interpretation_result,
)
from mh370_inverse_inference.reasoning import (
    ReasoningReason,
    ReasoningStatus,
    build_constrained_reasoning_request,
    build_constrained_reasoning_result,
    build_neutral_reasoning_trace,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _reasoning_lineage():
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
    reasoning_request = build_constrained_reasoning_request(
        interpretation_result,
        reasoning_policy_version="reasoning-1.0.0",
    )
    reasoning_result = build_constrained_reasoning_result(
        reasoning_request,
        status=ReasoningStatus.ACCEPTED,
        reason_codes=(ReasoningReason.OK,),
    )
    reasoning_trace = build_neutral_reasoning_trace(reasoning_result, records=())
    return reasoning_result, reasoning_trace


def _evaluation(index: int, claim_hash: str):
    reasoning_result, reasoning_trace = _reasoning_lineage()
    definition = build_hypothesis_definition(
        hypothesis_schema_version="1.0.0",
        hypothesis_type=HypothesisType.DESCRIPTIVE,
        statement=f"Neutral descriptive hypothesis {index}.",
        ordered_assumption_ids=(f"ASSUMPTION-{index:03d}",),
    )
    request = build_hypothesis_evaluation_request(
        reasoning_result,
        reasoning_trace,
        hypothesis_schema_version="1.0.0",
        evaluation_policy_version="evaluation-1.0.0",
        ordered_hypothesis_ids=(definition.hypothesis_id,),
        ordered_supporting_claim_hashes=(claim_hash,),
        ordered_contradicting_claim_hashes=(),
        permitted_claim_hashes=frozenset((claim_hash,)),
    )
    relation = build_evidence_hypothesis_relation_record(
        definition,
        claim_hash=claim_hash,
        permitted_claim_hashes=frozenset((claim_hash,)),
        relation_type=EvidenceHypothesisRelationType.SUPPORTS,
        relation_rule_id=f"RELATION-{index:03d}",
        relation_rule_version="1.0.0",
    )
    result = build_hypothesis_evaluation_result(
        request,
        relations=(relation,),
        ordered_outcomes=(HypothesisEvaluationOutcome.RETAINED,),
        status=HypothesisEvaluationStatus.COMPLETED,
        reason_codes=(HypothesisEvaluationReason.OK,),
    )
    trace = build_hypothesis_evaluation_trace(result, records=(relation,))
    return result, trace


def _comparative_lineage():
    first_result, first_trace = _evaluation(1, HASH_A)
    second_result, second_trace = _evaluation(2, HASH_D)
    return (first_result, second_result), (first_trace, second_trace)


def test_request_is_deterministic_and_content_addressed() -> None:
    results, traces = _comparative_lineage()
    first = build_comparative_assessment_request(
        results,
        traces,
        comparison_policy_version="comparison-1.0.0",
    )
    second = build_comparative_assessment_request(
        results,
        traces,
        comparison_policy_version="comparison-1.0.0",
    )

    assert first == second
    assert first.request_hash == sha256_payload(first.canonical_payload())
    assert first.ordered_evaluation_result_hashes == tuple(
        result.result_hash for result in results
    )
    assert first.ordered_evaluation_trace_hashes == tuple(
        trace.trace_hash for trace in traces
    )
    assert first.comparative_contract_version == "L6.0"


def test_request_is_frozen_and_constructor_is_disabled() -> None:
    results, traces = _comparative_lineage()
    request = build_comparative_assessment_request(
        results,
        traces,
        comparison_policy_version="comparison-1.0.0",
    )
    request_type: Any = ComparativeAssessmentRequest

    with pytest.raises(FrozenInstanceError):
        request.request_hash = HASH_A  # type: ignore[misc]

    with pytest.raises(TypeError):
        request_type(
            ordered_evaluation_result_hashes=(HASH_A, HASH_B),
            ordered_evaluation_trace_hashes=(HASH_C, HASH_D),
            comparison_policy_version="comparison-1.0.0",
            comparative_contract_version="L6.0",
            request_hash=HASH_A,
        )


def test_minimum_duplicate_and_lineage_guards() -> None:
    results, traces = _comparative_lineage()

    with pytest.raises(ValueError, match="at least two evaluation results"):
        build_comparative_assessment_request(
            results[:1],
            traces[:1],
            comparison_policy_version="comparison-1.0.0",
        )

    with pytest.raises(ValueError, match="duplicate result hashes"):
        build_comparative_assessment_request(
            (results[0], results[0]),
            (traces[0], traces[0]),
            comparison_policy_version="comparison-1.0.0",
        )

    with pytest.raises(ValueError, match="paired evaluation result"):
        build_comparative_assessment_request(
            results,
            (traces[1], traces[0]),
            comparison_policy_version="comparison-1.0.0",
        )


def test_payload_contains_only_contract_fields() -> None:
    results, traces = _comparative_lineage()
    request = build_comparative_assessment_request(
        results,
        traces,
        comparison_policy_version="comparison-1.0.0",
    )

    assert set(request.to_payload()) == {
        "comparison_policy_version",
        "comparative_contract_version",
        "ordered_evaluation_result_hashes",
        "ordered_evaluation_trace_hashes",
        "request_hash",
    }


def test_request_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/comparative/request.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "datetime",
        "uuid",
        "random",
        "requests",
        "socket",
        "probability",
        "confidence",
        "weight",
        "ranking",
        "bayesian",
        "trajectory",
        "drift",
        "endpoint",
        "coordinate",
        "location",
        "search_area",
        "filesystem",
        "pathlib",
        "database",
    )

    for token in forbidden:
        assert token not in source
