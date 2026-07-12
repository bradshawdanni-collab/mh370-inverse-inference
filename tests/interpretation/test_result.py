"""Tests for deterministic L3.4 interpretation result claim integration."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation import (
    ClaimStatus,
    InterpretationReason,
    InterpretationRequest,
    InterpretationResult,
    InterpretationStatus,
    NeutralClaimType,
    NeutralDerivedClaim,
    build_interpretation_request,
    build_interpretation_result,
    build_neutral_derived_claim,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


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


def _claim(
    *,
    claim_type: NeutralClaimType = NeutralClaimType.EVIDENCE_CONSUMED,
    supporting_evidence_ids: tuple[str, ...] = (HASH_A,),
    permitted_evidence_ids: frozenset[str] = frozenset((HASH_A, HASH_B, HASH_C)),
) -> NeutralDerivedClaim:
    return build_neutral_derived_claim(
        claim_type=claim_type,
        statement=f"Neutral structural claim: {claim_type.value}",
        supporting_evidence_ids=supporting_evidence_ids,
        permitted_evidence_ids=permitted_evidence_ids,
        interpretation_rule_id="neutral-rule",
        interpretation_rule_version="1.0.0",
        claim_status=ClaimStatus.ASSERTED,
    )


def _result(
    status: InterpretationStatus = InterpretationStatus.ACCEPTED,
    reason_codes: tuple[InterpretationReason, ...] = (InterpretationReason.OK,),
    derived_claims: tuple[NeutralDerivedClaim, ...] = (),
) -> InterpretationResult:
    return build_interpretation_result(
        _request(),
        interpretation_policy_version="interpretation-1.0.0",
        status=status,
        reason_codes=reason_codes,
        derived_claims=derived_claims,
    )


def test_empty_claim_result_remains_supported_and_deterministic() -> None:
    first = _result()
    second = _result()

    assert first == second
    assert first.input_hash == _request().input_hash
    assert first.result_hash == sha256_payload(first.canonical_payload())
    assert first.interpretation_contract_version == "L3.4"
    assert first.derived_claims == ()


def test_result_seals_neutral_claims_in_caller_order() -> None:
    first_claim = _claim(claim_type=NeutralClaimType.SOURCE_PRESENT)
    second_claim = _claim(claim_type=NeutralClaimType.VALIDATION_PASSED)

    result = _result(derived_claims=(first_claim, second_claim))

    assert result.derived_claims == (first_claim, second_claim)
    assert result.canonical_payload()["derived_claims"] == [
        first_claim.to_payload(),
        second_claim.to_payload(),
    ]
    assert result.result_hash == sha256_payload(result.canonical_payload())


def test_claim_order_changes_result_identity() -> None:
    first_claim = _claim(claim_type=NeutralClaimType.SOURCE_PRESENT)
    second_claim = _claim(claim_type=NeutralClaimType.OBSERVATION_LINKED)

    forward = _result(derived_claims=(first_claim, second_claim))
    reverse = _result(derived_claims=(second_claim, first_claim))

    assert forward.result_hash != reverse.result_hash


def test_duplicate_claim_hashes_are_rejected() -> None:
    claim = _claim()

    with pytest.raises(ValueError, match="duplicate claim hashes"):
        _result(derived_claims=(claim, claim))


def test_claims_outside_request_lineage_are_rejected() -> None:
    external_claim = _claim(
        supporting_evidence_ids=(HASH_D,),
        permitted_evidence_ids=frozenset((HASH_D,)),
    )

    with pytest.raises(ValueError, match="outside request lineage"):
        _result(derived_claims=(external_claim,))


def test_wrong_claim_container_and_values_are_rejected() -> None:
    builder: Any = build_interpretation_result

    with pytest.raises(TypeError):
        builder(
            _request(),
            interpretation_policy_version="interpretation-1.0.0",
            status=InterpretationStatus.ACCEPTED,
            reason_codes=(InterpretationReason.OK,),
            derived_claims=[_claim()],
        )
    with pytest.raises(TypeError):
        builder(
            _request(),
            interpretation_policy_version="interpretation-1.0.0",
            status=InterpretationStatus.ACCEPTED,
            reason_codes=(InterpretationReason.OK,),
            derived_claims=({"claim_hash": HASH_A},),
        )


def test_result_supports_all_neutral_statuses() -> None:
    rejected = _result(
        InterpretationStatus.REJECTED,
        (InterpretationReason.POLICY_REJECTED,),
    )
    insufficient = _result(
        InterpretationStatus.INSUFFICIENT_EVIDENCE,
        (InterpretationReason.INSUFFICIENT_EVIDENCE,),
    )

    assert rejected.status is InterpretationStatus.REJECTED
    assert insufficient.status is InterpretationStatus.INSUFFICIENT_EVIDENCE


def test_reason_order_is_part_of_result_identity() -> None:
    first = _result(
        InterpretationStatus.REJECTED,
        (
            InterpretationReason.POLICY_REJECTED,
            InterpretationReason.INSUFFICIENT_EVIDENCE,
        ),
    )
    second = _result(
        InterpretationStatus.REJECTED,
        (
            InterpretationReason.INSUFFICIENT_EVIDENCE,
            InterpretationReason.POLICY_REJECTED,
        ),
    )

    assert first.result_hash != second.result_hash


def test_result_and_claim_tuple_are_immutable() -> None:
    result = _result(derived_claims=(_claim(),))

    with pytest.raises(FrozenInstanceError):
        result.result_hash = HASH_A  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.derived_claims[0] = _claim()  # type: ignore[index]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    result_type: Any = InterpretationResult
    builder: Any = build_interpretation_result

    with pytest.raises(TypeError):
        result_type(
            input_hash=HASH_A,
            interpretation_contract_version="L3.4",
            interpretation_policy_version="interpretation-1.0.0",
            status=InterpretationStatus.ACCEPTED,
            reason_codes=(InterpretationReason.OK,),
            derived_claims=(),
            result_hash=HASH_B,
        )
    with pytest.raises(TypeError):
        builder(
            {"input_hash": HASH_A},
            interpretation_policy_version="interpretation-1.0.0",
            status=InterpretationStatus.ACCEPTED,
            reason_codes=(InterpretationReason.OK,),
        )


def test_result_payload_contains_only_neutral_contract_fields() -> None:
    result = _result(derived_claims=(_claim(),))

    assert set(result.to_payload()) == {
        "derived_claims",
        "input_hash",
        "interpretation_contract_version",
        "interpretation_policy_version",
        "reason_codes",
        "result_hash",
        "status",
    }


def test_result_module_excludes_authority_and_nondeterminism() -> None:
    module_path = Path("src/mh370_inverse_inference/interpretation/result.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "registry.py",
        "registration_models",
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
