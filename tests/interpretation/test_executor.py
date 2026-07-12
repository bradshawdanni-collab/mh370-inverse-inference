"""Tests for deterministic L3.5 neutral rule execution."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.interpretation import (
    ClaimStatus,
    InterpretationRequest,
    InterpretationStatus,
    NeutralClaimType,
    NeutralRuleExecution,
    NeutralRuleId,
    build_interpretation_request,
    execute_neutral_rule,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _request() -> InterpretationRequest:
    projection = AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )
    return build_interpretation_request(projection)


def _execute(rule_id: NeutralRuleId) -> NeutralRuleExecution:
    return execute_neutral_rule(
        _request(),
        rule_id=rule_id,
        interpretation_policy_version="interpretation-1.0.0",
    )


@pytest.mark.parametrize(
    ("rule_id", "claim_type", "support_id"),
    [
        (NeutralRuleId.SOURCE_PRESENT, NeutralClaimType.SOURCE_PRESENT, HASH_A),
        (
            NeutralRuleId.OBSERVATION_LINKED,
            NeutralClaimType.OBSERVATION_LINKED,
            HASH_A,
        ),
        (
            NeutralRuleId.VALIDATION_PRESENT,
            NeutralClaimType.VALIDATION_PASSED,
            HASH_C,
        ),
        (
            NeutralRuleId.EVIDENCE_CONSUMED,
            NeutralClaimType.EVIDENCE_CONSUMED,
            HASH_B,
        ),
    ],
)
def test_allowlisted_rules_emit_one_neutral_claim(
    rule_id: NeutralRuleId,
    claim_type: NeutralClaimType,
    support_id: str,
) -> None:
    execution = _execute(rule_id)
    claim = execution.result.derived_claims[0]

    assert execution.result.status is InterpretationStatus.ACCEPTED
    assert len(execution.result.derived_claims) == 1
    assert claim.claim_type is claim_type
    assert claim.claim_status is ClaimStatus.ASSERTED
    assert claim.supporting_evidence_ids == (support_id,)
    assert claim.interpretation_rule_id == rule_id.value
    assert claim.interpretation_rule_version == "1.0.0"


def test_execution_is_deterministic_and_content_addressed() -> None:
    first = _execute(NeutralRuleId.EVIDENCE_CONSUMED)
    second = _execute(NeutralRuleId.EVIDENCE_CONSUMED)

    assert first == second
    assert first.input_hash == _request().input_hash
    assert first.output_hash == first.result.result_hash
    assert len(first.op_signature_hash) == 64
    assert first.executor_contract_version == "L3.5"
    assert first.operation == "neutral_rule_execution"


def test_rule_identity_changes_operation_signature() -> None:
    first = _execute(NeutralRuleId.SOURCE_PRESENT)
    second = _execute(NeutralRuleId.VALIDATION_PRESENT)

    assert first.op_signature_hash != second.op_signature_hash
    assert first.output_hash != second.output_hash


def test_execution_record_is_frozen() -> None:
    execution = _execute(NeutralRuleId.OBSERVATION_LINKED)

    with pytest.raises(FrozenInstanceError):
        execution.output_hash = HASH_A  # type: ignore[misc]


def test_public_constructor_and_prohibited_inputs_are_rejected() -> None:
    execution_type: Any = NeutralRuleExecution
    executor: Any = execute_neutral_rule

    with pytest.raises(TypeError):
        execution_type(
            executor_contract_version="L3.5",
            operation="neutral_rule_execution",
            rule_id=NeutralRuleId.SOURCE_PRESENT,
            rule_version="1.0.0",
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            result=None,
        )
    with pytest.raises(TypeError):
        executor(
            {"input_hash": HASH_A},
            rule_id=NeutralRuleId.SOURCE_PRESENT,
            interpretation_policy_version="interpretation-1.0.0",
        )
    with pytest.raises(TypeError):
        executor(
            _request(),
            rule_id="SOURCE_PRESENT",
            interpretation_policy_version="interpretation-1.0.0",
        )


def test_blank_policy_version_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        execute_neutral_rule(
            _request(),
            rule_id=NeutralRuleId.SOURCE_PRESENT,
            interpretation_policy_version=" ",
        )


def test_execution_payload_contains_only_contract_fields() -> None:
    payload = _execute(NeutralRuleId.SOURCE_PRESENT).to_payload()

    assert set(payload) == {
        "executor_contract_version",
        "input_hash",
        "op_signature_hash",
        "operation",
        "output_hash",
        "result",
        "rule_id",
        "rule_version",
    }


def test_executor_module_excludes_authority_and_nondeterminism() -> None:
    module_path = Path("src/mh370_inverse_inference/interpretation/executor.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "registration_models",
        "registered_evidencerecord",
        "registry.py",
        "raw_evidence",
        "datetime",
        "uuid",
        "random",
        "requests",
        "socket",
        "pathlib",
        "likelihood",
        "bayesian",
        "trajectory",
        "endpoint",
        "location_claim",
    )

    for token in forbidden:
        assert token not in source
