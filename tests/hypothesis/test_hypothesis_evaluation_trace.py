"""Tests for the deterministic L5.4 hypothesis evaluation trace contract."""

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
    HypothesisEvaluationStatus,
    HypothesisEvaluationTrace,
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


def _result_and_records():
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
    definition = build_hypothesis_definition(
        hypothesis_schema_version="1.0.0",
        hypothesis_type=HypothesisType.DESCRIPTIVE,
        statement="A neutral descriptive hypothesis.",
        ordered_assumption_ids=("ASSUMPTION-001",),
    )
    request = build_hypothesis_evaluation_request(
        reasoning_result,
        reasoning_trace,
        hypothesis_schema_version="1.0.0",
        evaluation_policy_version="evaluation-1.0.0",
        ordered_hypothesis_ids=(definition.hypothesis_id,),
        ordered_supporting_claim_hashes=(HASH_A,),
        ordered_contradicting_claim_hashes=(),
        permitted_claim_hashes=frozenset((HASH_A,)),
    )
    relation = build_evidence_hypothesis_relation_record(
        definition,
        claim_hash=HASH_A,
        permitted_claim_hashes=frozenset((HASH_A,)),
        relation_type=EvidenceHypothesisRelationType.SUPPORTS,
        relation_rule_id="RELATION-001",
        relation_rule_version="1.0.0",
    )
    result = build_hypothesis_evaluation_result(
        request,
        relations=(relation,),
        ordered_outcomes=(HypothesisEvaluationOutcome.RETAINED,),
        status=HypothesisEvaluationStatus.COMPLETED,
        reason_codes=(HypothesisEvaluationReason.OK,),
    )
    return result, (relation,)


def test_trace_is_deterministic_and_content_addressed() -> None:
    result, records = _result_and_records()
    first = build_hypothesis_evaluation_trace(result, records=records)
    second = build_hypothesis_evaluation_trace(result, records=records)

    assert first == second
    assert first.trace_hash == sha256_payload(first.canonical_payload())
    assert first.evaluation_result_hash == result.result_hash
    assert first.ordered_relation_record_hashes == result.ordered_relation_record_hashes
    assert first.trace_contract_version == "L5.4"


def test_trace_is_frozen_and_constructor_is_disabled() -> None:
    result, records = _result_and_records()
    trace = build_hypothesis_evaluation_trace(result, records=records)
    trace_type: Any = HypothesisEvaluationTrace

    with pytest.raises(FrozenInstanceError):
        trace.trace_hash = HASH_A  # type: ignore[misc]

    with pytest.raises(TypeError):
        trace_type(
            evaluation_result_hash=HASH_A,
            ordered_relation_record_hashes=(HASH_B,),
            trace_contract_version="L5.4",
            trace_hash=HASH_C,
        )


def test_wrong_authority_and_duplicate_records_are_rejected() -> None:
    result, records = _result_and_records()
    builder: Any = build_hypothesis_evaluation_trace

    with pytest.raises(TypeError):
        builder({"result_hash": HASH_A}, records=records)

    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_hypothesis_evaluation_trace(
            result,
            records=(records[0], records[0]),
        )


def test_payload_contains_only_contract_fields() -> None:
    result, records = _result_and_records()
    trace = build_hypothesis_evaluation_trace(result, records=records)

    assert set(trace.to_payload()) == {
        "evaluation_result_hash",
        "ordered_relation_record_hashes",
        "trace_contract_version",
        "trace_hash",
    }


def test_trace_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/hypothesis/trace.py")
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