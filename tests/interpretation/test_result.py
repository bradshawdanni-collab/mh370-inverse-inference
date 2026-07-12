"""Tests for the deterministic L3.2 interpretation result envelope."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation import (
    InterpretationReason,
    InterpretationRequest,
    InterpretationResult,
    InterpretationStatus,
    build_interpretation_request,
    build_interpretation_result,
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


def _result(
    status: InterpretationStatus = InterpretationStatus.ACCEPTED,
    reason_codes: tuple[InterpretationReason, ...] = (InterpretationReason.OK,),
) -> InterpretationResult:
    return build_interpretation_result(
        _request(),
        interpretation_policy_version="interpretation-1.0.0",
        status=status,
        reason_codes=reason_codes,
    )


def test_result_is_deterministic_and_content_addressed() -> None:
    first = _result()
    second = _result()

    assert first == second
    assert first.input_hash == _request().input_hash
    assert first.result_hash == sha256_payload(first.canonical_payload())
    assert first.interpretation_contract_version == "L3.2"
    assert first.derived_claims == ()


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


def test_result_is_frozen() -> None:
    result = _result()

    with pytest.raises(FrozenInstanceError):
        result.result_hash = HASH_A  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    result_type: Any = InterpretationResult
    builder: Any = build_interpretation_result

    with pytest.raises(TypeError):
        result_type(
            input_hash=HASH_A,
            interpretation_contract_version="L3.2",
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
    result = _result()

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
