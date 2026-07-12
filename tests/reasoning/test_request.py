"""Tests for the deterministic L4.0 constrained reasoning input contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.interpretation import (
    ClaimStatus,
    InterpretationReason,
    InterpretationStatus,
    NeutralClaimType,
    build_interpretation_request,
    build_interpretation_result,
    build_neutral_derived_claim,
)
from mh370_inverse_inference.reasoning import (
    ConstrainedReasoningRequest,
    build_constrained_reasoning_request,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _interpretation_result(*, with_claim: bool = True):
    projection = AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )
    request = build_interpretation_request(projection)
    claims = ()
    if with_claim:
        claim = build_neutral_derived_claim(
            claim_type=NeutralClaimType.EVIDENCE_CONSUMED,
            statement="Accepted evidence projection was consumed.",
            supporting_evidence_ids=(HASH_B,),
            permitted_evidence_ids=frozenset((HASH_A, HASH_B, HASH_C)),
            interpretation_rule_id="EVIDENCE_CONSUMED",
            interpretation_rule_version="1.0.0",
            claim_status=ClaimStatus.ASSERTED,
        )
        claims = (claim,)
    return build_interpretation_result(
        request,
        interpretation_policy_version="interpretation-1.0.0",
        status=InterpretationStatus.ACCEPTED,
        reason_codes=(InterpretationReason.OK,),
        derived_claims=claims,
    )


def test_request_is_deterministic_and_content_addressed() -> None:
    result = _interpretation_result()

    first = build_constrained_reasoning_request(
        result,
        reasoning_policy_version="reasoning-1.0.0",
    )
    second = build_constrained_reasoning_request(
        result,
        reasoning_policy_version="reasoning-1.0.0",
    )

    assert first == second
    assert first.request_hash == second.request_hash
    assert first.interpretation_result_hash == result.result_hash
    assert first.interpretation_input_hash == result.input_hash
    assert first.reasoning_contract_version == "L4.0"
    assert first.ordered_claim_hashes == tuple(
        claim.claim_hash for claim in result.derived_claims
    )


def test_empty_claim_result_remains_valid() -> None:
    request = build_constrained_reasoning_request(
        _interpretation_result(with_claim=False),
        reasoning_policy_version="reasoning-1.0.0",
    )

    assert request.ordered_claim_hashes == ()


def test_request_is_frozen() -> None:
    request = build_constrained_reasoning_request(
        _interpretation_result(),
        reasoning_policy_version="reasoning-1.0.0",
    )

    with pytest.raises(FrozenInstanceError):
        request.request_hash = HASH_A  # type: ignore[misc]


def test_public_constructor_and_prohibited_inputs_are_rejected() -> None:
    request_type: Any = ConstrainedReasoningRequest
    builder: Any = build_constrained_reasoning_request

    with pytest.raises(TypeError):
        request_type(
            interpretation_result_hash=HASH_A,
            interpretation_input_hash=HASH_B,
            interpretation_contract_version="L3.4",
            ordered_claim_hashes=(HASH_C,),
            reasoning_policy_version="reasoning-1.0.0",
            reasoning_contract_version="L4.0",
            request_hash=HASH_A,
        )

    for value in ({"result_hash": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(value, reasoning_policy_version="reasoning-1.0.0")


def test_policy_version_participates_in_request_identity() -> None:
    result = _interpretation_result()
    first = build_constrained_reasoning_request(
        result,
        reasoning_policy_version="reasoning-1.0.0",
    )
    second = build_constrained_reasoning_request(
        result,
        reasoning_policy_version="reasoning-2.0.0",
    )

    assert first.request_hash != second.request_hash


def test_reasoning_module_excludes_authority_and_inference_dependencies() -> None:
    package_root = (
        Path(__file__).parents[2] / "src" / "mh370_inverse_inference" / "reasoning"
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package_root.glob("*.py"))
    ).lower()

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
        "bayesian",
        "trajectory",
        "endpoint",
        "location",
    )

    for token in forbidden:
        assert token not in source
