"""Tests for the deterministic L4.3 neutral reasoning trace contract."""

from dataclasses import FrozenInstanceError, fields
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
    ConstrainedReasoningResult,
    NeutralReasoningTrace,
    ReasoningReason,
    ReasoningStatus,
    RuleApplicationOutcome,
    RuleApplicationReason,
    RuleApplicationRecord,
    build_constrained_reasoning_request,
    build_constrained_reasoning_result,
    build_neutral_reasoning_trace,
    build_rule_application_record,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _reasoning_result(
    *,
    reasoning_policy_version: str = "reasoning-1.0.0",
) -> ConstrainedReasoningResult:
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
        reasoning_policy_version=reasoning_policy_version,
    )
    return build_constrained_reasoning_result(
        reasoning_input,
        status=ReasoningStatus.ACCEPTED,
        reason_codes=(ReasoningReason.OK,),
    )


def _record(
    result: ConstrainedReasoningResult,
    *,
    rule_id: str,
) -> RuleApplicationRecord:
    return build_rule_application_record(
        result,
        rule_id=rule_id,
        rule_version="1.0.0",
        input_claim_hashes=(),
        permitted_claim_hashes=frozenset(),
        outcome=RuleApplicationOutcome.APPLIED,
        reason_codes=(RuleApplicationReason.OK,),
    )


def _trace() -> NeutralReasoningTrace:
    result = _reasoning_result()
    records = (
        _record(result, rule_id="RULE-001"),
        _record(result, rule_id="RULE-002"),
    )
    return build_neutral_reasoning_trace(result, records=records)


def test_trace_is_deterministic_and_content_addressed() -> None:
    first = _trace()
    second = _trace()

    assert first == second
    assert first.trace_contract_version == "L4.3"
    assert first.trace_hash == sha256_payload(first.canonical_payload())
    assert first.reasoning_result_hash == _reasoning_result().result_hash


def test_record_order_is_part_of_trace_identity() -> None:
    result = _reasoning_result()
    first_record = _record(result, rule_id="RULE-001")
    second_record = _record(result, rule_id="RULE-002")

    first = build_neutral_reasoning_trace(
        result,
        records=(first_record, second_record),
    )
    second = build_neutral_reasoning_trace(
        result,
        records=(second_record, first_record),
    )

    assert first.trace_hash != second.trace_hash


def test_empty_trace_is_deterministic() -> None:
    result = _reasoning_result()

    first = build_neutral_reasoning_trace(result, records=())
    second = build_neutral_reasoning_trace(result, records=())

    assert first == second
    assert first.ordered_rule_application_hashes == ()


def test_duplicate_records_are_rejected() -> None:
    result = _reasoning_result()
    record = _record(result, rule_id="RULE-001")

    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_neutral_reasoning_trace(result, records=(record, record))


def test_mismatched_result_lineage_is_rejected() -> None:
    result = _reasoning_result()
    other_result = _reasoning_result(reasoning_policy_version="reasoning-2.0.0")
    record = _record(other_result, rule_id="RULE-001")

    with pytest.raises(ValueError, match="supplied reasoning result"):
        build_neutral_reasoning_trace(result, records=(record,))


def test_trace_is_frozen() -> None:
    trace = _trace()

    with pytest.raises(FrozenInstanceError):
        trace.trace_hash = HASH_A  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    trace_type: Any = NeutralReasoningTrace
    builder: Any = build_neutral_reasoning_trace

    with pytest.raises(TypeError):
        trace_type(
            reasoning_result_hash=HASH_A,
            ordered_rule_application_hashes=(HASH_B,),
            trace_contract_version="L4.3",
            trace_hash=HASH_C,
        )

    for value in ({"result_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(value, records=())

    result = _reasoning_result()
    with pytest.raises(TypeError):
        builder(result, records=(object(),))


def test_trace_surface_contains_only_contract_fields() -> None:
    trace = _trace()

    assert tuple(field.name for field in fields(trace)) == (
        "reasoning_result_hash",
        "ordered_rule_application_hashes",
        "trace_contract_version",
        "trace_hash",
    )
    assert set(trace.to_payload()) == {
        "ordered_rule_application_hashes",
        "reasoning_result_hash",
        "trace_contract_version",
        "trace_hash",
    }


def test_trace_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/reasoning/trace.py")
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
        "database",
    )

    for token in forbidden:
        assert token not in source
