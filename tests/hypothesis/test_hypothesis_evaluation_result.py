"""Tests for the deterministic L5.3 hypothesis evaluation result contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    EvidenceHypothesisRelationType,
    HypothesisEvaluationOutcome,
    HypothesisEvaluationReason,
    HypothesisEvaluationResult,
    HypothesisEvaluationStatus,
    HypothesisType,
    build_evidence_hypothesis_relation_record,
    build_hypothesis_definition,
    build_hypothesis_evaluation_request,
    build_hypothesis_evaluation_result,
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


def _request_and_relations():
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
        reasoning_policy_version="reasoning-1.0.0",
    )
    reasoning_result = build_constrained_reasoning_result(
        reasoning_input,
        status=ReasoningStatus.ACCEPTED,
        reason_codes=(ReasoningReason.OK,),
    )
    reasoning_trace = build_neutral_reasoning_trace(reasoning_result, records=())
    first_definition = build_hypothesis_definition(
        hypothesis_schema_version="1.0.0",
        hypothesis_type=HypothesisType.DESCRIPTIVE,
        statement="A neutral descriptive hypothesis.",
        ordered_assumption_ids=("ASSUMPTION-001",),
    )
    second_definition = build_hypothesis_definition(
        hypothesis_schema_version="1.0.0",
        hypothesis_type=HypothesisType.CONSTRAINT,
        statement="A neutral constraint hypothesis.",
        ordered_assumption_ids=("ASSUMPTION-002",),
    )
    request = build_hypothesis_evaluation_request(
        reasoning_result,
        reasoning_trace,
        hypothesis_schema_version="1.0.0",
        evaluation_policy_version="evaluation-1.0.0",
        ordered_hypothesis_ids=(
            first_definition.hypothesis_id,
            second_definition.hypothesis_id,
        ),
        ordered_supporting_claim_hashes=(HASH_A,),
        ordered_contradicting_claim_hashes=(HASH_B,),
        permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
    )
    first_relation = build_evidence_hypothesis_relation_record(
        first_definition,
        claim_hash=HASH_A,
        permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
        relation_type=EvidenceHypothesisRelationType.SUPPORTS,
        relation_rule_id="RELATION-001",
        relation_rule_version="1.0.0",
    )
    second_relation = build_evidence_hypothesis_relation_record(
        second_definition,
        claim_hash=HASH_B,
        permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
        relation_type=EvidenceHypothesisRelationType.CONTRADICTS,
        relation_rule_id="RELATION-002",
        relation_rule_version="1.0.0",
    )
    return request, (first_relation, second_relation)


def _result(
    *,
    outcomes: tuple[HypothesisEvaluationOutcome, ...] = (
        HypothesisEvaluationOutcome.RETAINED,
        HypothesisEvaluationOutcome.REJECTED,
    ),
    status: HypothesisEvaluationStatus = HypothesisEvaluationStatus.COMPLETED,
    reasons: tuple[HypothesisEvaluationReason, ...] = (
        HypothesisEvaluationReason.OK,
    ),
) -> HypothesisEvaluationResult:
    request, relations = _request_and_relations()
    return build_hypothesis_evaluation_result(
        request,
        relations=relations,
        ordered_outcomes=outcomes,
        status=status,
        reason_codes=reasons,
    )


def test_result_is_deterministic_and_content_addressed() -> None:
    first = _result()
    second = _result()

    assert first == second
    assert first.result_hash == second.result_hash
    assert first.result_hash == sha256_payload(first.canonical_payload())
    assert first.evaluation_result_contract_version == "L5.3"


def test_request_identity_and_policy_are_preserved() -> None:
    request, relations = _request_and_relations()
    result = build_hypothesis_evaluation_result(
        request,
        relations=relations,
        ordered_outcomes=(
            HypothesisEvaluationOutcome.RETAINED,
            HypothesisEvaluationOutcome.REJECTED,
        ),
        status=HypothesisEvaluationStatus.COMPLETED,
        reason_codes=(HypothesisEvaluationReason.OK,),
    )

    assert result.request_hash == request.request_hash
    assert result.evaluation_policy_version == request.evaluation_policy_version
    assert result.ordered_hypothesis_ids == request.ordered_hypothesis_ids


def test_order_is_part_of_result_identity() -> None:
    first = _result()
    second = _result(
        outcomes=(
            HypothesisEvaluationOutcome.REJECTED,
            HypothesisEvaluationOutcome.RETAINED,
        )
    )
    third = _result(
        status=HypothesisEvaluationStatus.REJECTED,
        reasons=(
            HypothesisEvaluationReason.POLICY_REJECTED,
            HypothesisEvaluationReason.INSUFFICIENT_BASIS,
        ),
    )
    fourth = _result(
        status=HypothesisEvaluationStatus.REJECTED,
        reasons=(
            HypothesisEvaluationReason.INSUFFICIENT_BASIS,
            HypothesisEvaluationReason.POLICY_REJECTED,
        ),
    )

    assert first.result_hash != second.result_hash
    assert third.result_hash != fourth.result_hash


def test_all_statuses_and_outcomes_are_supported() -> None:
    statuses = tuple(HypothesisEvaluationStatus)
    outcomes = tuple(HypothesisEvaluationOutcome)

    for status in statuses:
        result = _result(
            outcomes=(outcomes[0], outcomes[1]),
            status=status,
            reasons=(HypothesisEvaluationReason.OK,),
        )
        assert result.status is status


def test_duplicate_and_misaligned_inputs_are_rejected() -> None:
    request, relations = _request_and_relations()

    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_hypothesis_evaluation_result(
            request,
            relations=(relations[0], relations[0]),
            ordered_outcomes=(
                HypothesisEvaluationOutcome.RETAINED,
                HypothesisEvaluationOutcome.REJECTED,
            ),
            status=HypothesisEvaluationStatus.COMPLETED,
            reason_codes=(HypothesisEvaluationReason.OK,),
        )

    with pytest.raises(ValueError, match="must align"):
        build_hypothesis_evaluation_result(
            request,
            relations=relations,
            ordered_outcomes=(HypothesisEvaluationOutcome.RETAINED,),
            status=HypothesisEvaluationStatus.COMPLETED,
            reason_codes=(HypothesisEvaluationReason.OK,),
        )


def test_result_is_frozen_and_constructor_is_disabled() -> None:
    result = _result()
    result_type: Any = HypothesisEvaluationResult

    with pytest.raises(FrozenInstanceError):
        result.result_hash = HASH_A  # type: ignore[misc]

    with pytest.raises(TypeError):
        result_type(
            request_hash=HASH_A,
            evaluation_policy_version="evaluation-1.0.0",
            ordered_hypothesis_ids=(HASH_B,),
            ordered_relation_record_hashes=(HASH_C,),
            ordered_outcomes=(HypothesisEvaluationOutcome.RETAINED,),
            status=HypothesisEvaluationStatus.COMPLETED,
            reason_codes=(HypothesisEvaluationReason.OK,),
            evaluation_result_contract_version="L5.3",
            result_hash=HASH_A,
        )


def test_wrong_authority_is_rejected() -> None:
    builder: Any = build_hypothesis_evaluation_result

    for value in ({"request_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(
                value,
                relations=(),
                ordered_outcomes=(),
                status=HypothesisEvaluationStatus.REJECTED,
                reason_codes=(HypothesisEvaluationReason.POLICY_REJECTED,),
            )


def test_payload_contains_only_contract_fields() -> None:
    assert set(_result().to_payload()) == {
        "evaluation_policy_version",
        "evaluation_result_contract_version",
        "ordered_hypothesis_ids",
        "ordered_outcomes",
        "ordered_relation_record_hashes",
        "reason_codes",
        "request_hash",
        "result_hash",
        "status",
    }


def test_result_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/hypothesis/result.py")
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
        "filesystem",
        "pathlib",
        "database",
    )

    for token in forbidden:
        assert token not in source
