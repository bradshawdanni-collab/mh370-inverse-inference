"""Tests for L3.6 shared trace mapping and deterministic replay."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.engine.trace import TraceStatus
from mh370_inverse_inference.interpretation import (
    InterpretationReason,
    InterpretationStatus,
    NeutralRuleId,
    build_interpretation_request,
    build_interpretation_result,
    execute_neutral_rule,
)
from mh370_inverse_inference.interpretation.trace_adapter import (
    STAGE_ID,
    build_nonaccepted_interpretation_trace,
    neutral_rule_execution_to_trace,
    verify_interpretation_trace,
)

FIXTURE_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "interpretation"
    / "l3_6_replay_case_001.json"
)


def _fixture() -> dict[str, Any]:
    loaded = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _request_from_fixture() -> Any:
    fixture = _fixture()
    projection_data = fixture["projection"]
    projection = AcceptedEvidenceProjection(**projection_data)
    return build_interpretation_request(projection)


def test_replay_fixture_is_deterministic() -> None:
    fixture = _fixture()
    request = _request_from_fixture()
    rule_id = NeutralRuleId(fixture["rule_id"])

    first = execute_neutral_rule(
        request,
        rule_id=rule_id,
        interpretation_policy_version=fixture["interpretation_policy_version"],
    )
    second = execute_neutral_rule(
        request,
        rule_id=rule_id,
        interpretation_policy_version=fixture["interpretation_policy_version"],
    )
    first_trace = neutral_rule_execution_to_trace(
        first,
        stage_index=fixture["stage_index"],
    )
    second_trace = neutral_rule_execution_to_trace(
        second,
        stage_index=fixture["stage_index"],
    )

    assert first == second
    assert first_trace == second_trace
    assert first_trace.stage_id == fixture["stage_id"] == STAGE_ID
    assert first_trace.input_hash == request.input_hash
    assert first_trace.output_hash == first.result.result_hash
    assert first_trace.op_signature_hash == first.op_signature_hash
    assert first_trace.status is TraceStatus.OK
    assert first_trace.record_count == 1
    assert verify_interpretation_trace(first_trace)


def test_trace_metadata_preserves_ordered_claim_hashes() -> None:
    fixture = _fixture()
    execution = execute_neutral_rule(
        _request_from_fixture(),
        rule_id=NeutralRuleId(fixture["rule_id"]),
        interpretation_policy_version=fixture["interpretation_policy_version"],
    )
    trace = neutral_rule_execution_to_trace(
        execution,
        stage_index=fixture["stage_index"],
    )
    metadata = json.loads(trace.metadata_json or "{}")

    assert metadata["claim_hashes"] == [
        claim.claim_hash for claim in execution.result.derived_claims
    ]
    assert metadata["rule_id"] == execution.rule_id.value
    assert metadata["rule_version"] == execution.rule_version


def test_withheld_and_insufficient_support_outcomes_map_to_trace() -> None:
    request = _request_from_fixture()
    op_signature_hash = sha256_payload({"operation": "neutral_rule_execution"})
    withheld = build_interpretation_result(
        request,
        interpretation_policy_version="interpretation-1.0.0",
        status=InterpretationStatus.REJECTED,
        reason_codes=(InterpretationReason.POLICY_REJECTED,),
    )
    insufficient = build_interpretation_result(
        request,
        interpretation_policy_version="interpretation-1.0.0",
        status=InterpretationStatus.INSUFFICIENT_EVIDENCE,
        reason_codes=(InterpretationReason.INSUFFICIENT_EVIDENCE,),
    )

    withheld_trace = build_nonaccepted_interpretation_trace(
        withheld,
        op_signature_hash=op_signature_hash,
        rule_id="EVIDENCE_CONSUMED",
        rule_version="1.0.0",
        stage_index=6,
    )
    insufficient_trace = build_nonaccepted_interpretation_trace(
        insufficient,
        op_signature_hash=op_signature_hash,
        rule_id="EVIDENCE_CONSUMED",
        rule_version="1.0.0",
        stage_index=6,
    )

    assert withheld_trace.status is TraceStatus.FAILED
    assert withheld_trace.failure_kind == InterpretationReason.POLICY_REJECTED.value
    assert insufficient_trace.status is TraceStatus.PARTIAL
    assert insufficient_trace.failure_kind is None
    assert withheld_trace.record_count == 0
    assert insufficient_trace.record_count == 0


def test_trace_tampering_is_detected() -> None:
    fixture = _fixture()
    execution = execute_neutral_rule(
        _request_from_fixture(),
        rule_id=NeutralRuleId(fixture["rule_id"]),
        interpretation_policy_version=fixture["interpretation_policy_version"],
    )
    trace = neutral_rule_execution_to_trace(execution, stage_index=6)
    tampered = replace(trace, trace_hash="d" * 64)

    assert verify_interpretation_trace(trace)
    assert not verify_interpretation_trace(tampered)


def test_trace_adapter_rejects_wrong_authority() -> None:
    adapter: Any = neutral_rule_execution_to_trace

    with pytest.raises(TypeError):
        adapter({"input_hash": "a" * 64}, stage_index=6)
