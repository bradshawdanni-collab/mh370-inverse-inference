"""Tests for the deterministic L3.3 neutral derived claim contract."""

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation.claim import (
    ClaimStatus,
    NeutralClaimType,
    NeutralDerivedClaim,
    build_neutral_derived_claim,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _claim(
    *,
    claim_status: ClaimStatus = ClaimStatus.ASSERTED,
    rule_version: str = "1.0.0",
) -> NeutralDerivedClaim:
    return build_neutral_derived_claim(
        claim_type=NeutralClaimType.EVIDENCE_CONSUMED,
        statement="Accepted evidence was consumed by the interpretation boundary.",
        supporting_evidence_ids=(HASH_A,),
        permitted_evidence_ids=frozenset({HASH_A, HASH_B}),
        interpretation_rule_id="rule-evidence-consumed",
        interpretation_rule_version=rule_version,
        claim_status=claim_status,
    )


def test_claim_is_deterministic_and_content_addressed() -> None:
    first = _claim()
    second = _claim()

    assert first == second
    assert first.claim_id == first.claim_hash
    assert first.claim_hash == sha256_payload(first.canonical_payload())
    assert first.claim_contract_version == "L3.3"


def test_claim_identity_changes_with_status_or_rule_version() -> None:
    asserted = _claim()
    withheld = _claim(claim_status=ClaimStatus.WITHHELD)
    revised = _claim(rule_version="1.0.1")

    assert asserted.claim_hash != withheld.claim_hash
    assert asserted.claim_hash != revised.claim_hash


def test_claim_rejects_evidence_outside_permitted_lineage() -> None:
    with pytest.raises(ValueError, match="outside permitted lineage"):
        build_neutral_derived_claim(
            claim_type=NeutralClaimType.SOURCE_PRESENT,
            statement="A source is present.",
            supporting_evidence_ids=(HASH_B,),
            permitted_evidence_ids=frozenset({HASH_A}),
            interpretation_rule_id="rule-source-present",
            interpretation_rule_version="1.0.0",
            claim_status=ClaimStatus.ASSERTED,
        )


def test_claim_is_frozen_and_public_constructor_is_disabled() -> None:
    claim = _claim()
    claim_type: Any = NeutralDerivedClaim

    with pytest.raises(FrozenInstanceError):
        claim.statement = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        claim_type(
            claim_id=HASH_A,
            claim_type=NeutralClaimType.RULE_APPLIED,
            statement="Rule applied.",
            supporting_evidence_ids=(HASH_A,),
            interpretation_rule_id="rule-1",
            interpretation_rule_version="1.0.0",
            claim_status=ClaimStatus.ASSERTED,
            claim_hash=HASH_A,
            claim_contract_version="L3.3",
        )


def test_claim_fields_are_exactly_the_l33_contract_surface() -> None:
    assert tuple(field.name for field in fields(NeutralDerivedClaim)) == (
        "claim_id",
        "claim_type",
        "statement",
        "supporting_evidence_ids",
        "interpretation_rule_id",
        "interpretation_rule_version",
        "claim_status",
        "claim_hash",
        "claim_contract_version",
    )


def test_claim_module_excludes_inference_and_side_effects() -> None:
    module_path = Path("src/mh370_inverse_inference/interpretation/claim.py")
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
        "probability",
        "bayesian",
        "ranking",
        "trajectory",
        "endpoint",
        "latitude",
        "longitude",
        "location_claim",
    )

    for token in forbidden:
        assert token not in source
