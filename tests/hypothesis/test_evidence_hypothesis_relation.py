"""Tests for the deterministic L5.2 relation-record contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    EvidenceHypothesisRelationRecord,
    EvidenceHypothesisRelationType,
    HypothesisDefinition,
    HypothesisType,
    build_evidence_hypothesis_relation_record,
    build_hypothesis_definition,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _definition(
    assumption_ids: tuple[str, ...] = ("assumption-001",),
) -> HypothesisDefinition:
    return build_hypothesis_definition(
        hypothesis_schema_version="hypothesis-1.0.0",
        hypothesis_type=HypothesisType.DESCRIPTIVE,
        statement="A neutral structural proposition is present.",
        ordered_assumption_ids=assumption_ids,
    )


def _record(
    relation_type: EvidenceHypothesisRelationType = (
        EvidenceHypothesisRelationType.SUPPORTS
    ),
) -> EvidenceHypothesisRelationRecord:
    return build_evidence_hypothesis_relation_record(
        _definition(),
        claim_hash=HASH_A,
        permitted_claim_hashes=frozenset((HASH_A, HASH_B)),
        relation_type=relation_type,
        relation_rule_id="RELATION-RULE-001",
        relation_rule_version="1.0.0",
    )


def test_record_is_deterministic_and_content_addressed() -> None:
    first = _record()
    second = _record()

    assert first == second
    assert first.hypothesis_id == _definition().hypothesis_id
    assert first.hypothesis_definition_hash == _definition().definition_hash
    assert first.hypothesis_id == first.hypothesis_definition_hash
    assert first.relation_contract_version == "L5.2"
    assert first.record_hash == sha256_payload(first.canonical_payload())


def test_record_supports_both_structural_relation_types() -> None:
    for relation_type in EvidenceHypothesisRelationType:
        record = _record(relation_type)
        assert record.relation_type is relation_type


def test_relation_type_is_part_of_record_identity() -> None:
    supporting = _record(EvidenceHypothesisRelationType.SUPPORTS)
    contradicting = _record(EvidenceHypothesisRelationType.CONTRADICTS)

    assert supporting.record_hash != contradicting.record_hash


def test_unpermitted_claim_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside permitted lineage"):
        build_evidence_hypothesis_relation_record(
            _definition(),
            claim_hash=HASH_B,
            permitted_claim_hashes=frozenset((HASH_A,)),
            relation_type=EvidenceHypothesisRelationType.SUPPORTS,
            relation_rule_id="RELATION-RULE-001",
            relation_rule_version="1.0.0",
        )


def test_malformed_claim_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        build_evidence_hypothesis_relation_record(
            _definition(),
            claim_hash="not-a-digest",
            permitted_claim_hashes=frozenset(("not-a-digest",)),
            relation_type=EvidenceHypothesisRelationType.SUPPORTS,
            relation_rule_id="RELATION-RULE-001",
            relation_rule_version="1.0.0",
        )


@pytest.mark.parametrize("field", ("relation_rule_id", "relation_rule_version"))
def test_blank_rule_metadata_is_rejected(field: str) -> None:
    values = {
        "relation_rule_id": "RELATION-RULE-001",
        "relation_rule_version": "1.0.0",
    }
    values[field] = " "

    with pytest.raises(ValueError, match="cannot be blank"):
        build_evidence_hypothesis_relation_record(
            _definition(),
            claim_hash=HASH_A,
            permitted_claim_hashes=frozenset((HASH_A,)),
            relation_type=EvidenceHypothesisRelationType.SUPPORTS,
            relation_rule_id=values["relation_rule_id"],
            relation_rule_version=values["relation_rule_version"],
        )


def test_record_is_frozen() -> None:
    record = _record()

    with pytest.raises(FrozenInstanceError):
        record.record_hash = HASH_B  # type: ignore[misc]


def test_public_constructor_and_wrong_authority_are_rejected() -> None:
    record_type: Any = EvidenceHypothesisRelationRecord
    builder: Any = build_evidence_hypothesis_relation_record

    with pytest.raises(TypeError):
        record_type(
            hypothesis_id=HASH_A,
            hypothesis_definition_hash=HASH_A,
            claim_hash=HASH_B,
            relation_type=EvidenceHypothesisRelationType.SUPPORTS,
            relation_rule_id="RELATION-RULE-001",
            relation_rule_version="1.0.0",
            relation_contract_version="L5.2",
            record_hash=HASH_A,
        )

    for value in ({"hypothesis_id": HASH_A}, HASH_A, object()):
        with pytest.raises(TypeError):
            builder(
                value,
                claim_hash=HASH_B,
                permitted_claim_hashes=frozenset((HASH_B,)),
                relation_type=EvidenceHypothesisRelationType.SUPPORTS,
                relation_rule_id="RELATION-RULE-001",
                relation_rule_version="1.0.0",
            )


def test_record_payload_contains_only_contract_fields() -> None:
    record = _record()

    assert set(record.to_payload()) == {
        "claim_hash",
        "hypothesis_definition_hash",
        "hypothesis_id",
        "record_hash",
        "relation_contract_version",
        "relation_rule_id",
        "relation_rule_version",
        "relation_type",
    }


def test_relation_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/hypothesis/relation.py")
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
