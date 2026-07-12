"""Tests for the deterministic L4.2 rule application record contract."""

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
    ConstrainedReasoningResult,
    ReasoningReason,
    ReasoningStatus,
    RuleApplicationOutcome,
    RuleApplicationReason,
    RuleApplicationRecord,
    build_constrained_reasoning_request,
    build_constrained_reasoning_result,
    build_rule_application_record,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _reasoning_result() -> ConstrainedReasoningResult:
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
    return build_constrained_reasoning_result(
        reasoning_input,
        status=ReasoningStatus.ACCEPTED,
        reason_codes=(ReasoningReason.OK,),
    )


def _record(
    *,
    input_claim_hashes: tuple[str, ...] = (HASH_A, HASH_B),
    outcome: RuleApplicationOutcome = RuleApplicationOutcome.APPLIED,
    reason_codes: tuple[RuleApplicationReason, ...] = (
        RuleApplicationReason.OK,
    ),
) -> RuleApplicationRecord:
    return build_rule_application_record(
        _reasoning_result(),
        rule_id="RULE-001",
        rule_version="1.0.0",
        input_claim_hashes=input_claim_hashes,
        permitted_claim_hashes=frozenset((HASH_A, HASH_B, HASH_C)),
        outcome=outcome,
        reason_codes=reason_codes,
    )


def test_record_is_deterministic_and_content_addressed() -> None:
    first = _record()
    second = _record()

    assert first == second
    assert first.reasoning_result_hash == _reasoning_result().result_hash
    assert first.rule_application_contract_version == "L4.2"
    assert first.record_hash == sha256_payload(first.canonical_payload())


def test_claim_and_reason_order_are_part_of_identity() -> None:
    claim_first = _record(input_claim_hashes=(HASH_A, HASH_B))
    claim_second = _record(input_claim_hashes=(HASH_B, HASH_A))
    reason_first = _record(
        reason_codes=(
            RuleApplicationReason.RULE_NOT_SATISFIED,
            RuleApplicationReason.INSUFFICIENT_BASIS,
        )
    )
    reason_second = _record(
        reason_codes=(
            RuleApplicationReason.INSUFFICIENT_BASIS,
            RuleApplicationReason.RULE_NOT_SATISFIED,
        )
    )

    assert claim_first.record_hash != claim_second.record_hash
    assert reason_first.record_hash != reason_second.record_hash


def test_record_supports_all_neutral_outcomes() -> None:
    cases = (
        (RuleApplicationOutcome.APPLIED, RuleApplicationReason.OK),
        (
            RuleApplicationOutcome.NOT_APPLIED,
            RuleApplicationReason.RULE_NOT_SATISFIED,
        ),
        (
            RuleApplicationOutcome.INSUFFICIENT_BASIS,
            RuleApplicationReason.INSUFFICIENT_BASIS,
        ),
        (
            RuleApplicationOutcome.CONSTRAINT_BLOCKED,
            RuleApplicationReason.CONSTRAINT_BLOCKED,
        ),
    )

    for outcome, reason in cases:
        record = _record(outcome=outcome, reason_codes=(reason,))
        assert record.outcome is outcome
        assert record.reason_codes == (reason,)


def test_unpermitted_claim_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside permitted lineage"):
        build_rule_application_record(
            _reasoning_result(),
            rule_id="RULE-001",
            rule_version="1.0.0",
            input_claim_hashes=(HASH_C,),
            permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
            outcome=RuleApplicationOutcome.NOT_APPLIED,
            reason_codes=(RuleApplicationReason.RULE_NOT_SATISFIED,),
        )


def test_record_is_frozen() -> None:
    record = _record()

    with pytest.raises(FrozenInstanceError):
        record.record_hash = HASH_C  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    record_type: Any = RuleApplicationRecord
    builder: Any = build_rule_application_record

    with pytest.raises(TypeError):
        record_type(
            reasoning_result_hash=HASH_A,
            rule_id="RULE-001",
            rule_version="1.0.0",
            input_claim_hashes=(HASH_B,),
            outcome=RuleApplicationOutcome.APPLIED,
            reason_codes=(RuleApplicationReason.OK,),
            rule_application_contract_version="L4.2",
            record_hash=HASH_C,
        )

    for value in ({"result_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(
                value,
                rule_id="RULE-001",
                rule_version="1.0.0",
                input_claim_hashes=(),
                permitted_claim_hashes=frozenset(),
                outcome=RuleApplicationOutcome.NOT_APPLIED,
                reason_codes=(RuleApplicationReason.RULE_NOT_SATISFIED,),
            )


def test_record_payload_contains_only_contract_fields() -> None:
    record = _record()

    assert set(record.to_payload()) == {
        "input_claim_hashes",
        "outcome",
        "reason_codes",
        "reasoning_result_hash",
        "record_hash",
        "rule_application_contract_version",
        "rule_id",
        "rule_version",
    }


def test_application_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/reasoning/application.py")
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
