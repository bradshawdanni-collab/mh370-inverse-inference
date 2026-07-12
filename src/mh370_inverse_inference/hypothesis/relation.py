"""Immutable deterministic L5.2 evidence-hypothesis relation contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis.definition import HypothesisDefinition

CONTRACT_VERSION = "L5.2"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EvidenceHypothesisRelationType(StrEnum):
    """Stable structural relations between one claim and one hypothesis."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class EvidenceHypothesisRelationRecord:
    """Content-addressed structural relation bound to one hypothesis."""

    hypothesis_id: str
    hypothesis_definition_hash: str
    claim_hash: str
    relation_type: EvidenceHypothesisRelationType
    relation_rule_id: str
    relation_rule_version: str
    relation_contract_version: str
    record_hash: str

    @classmethod
    def _from_definition(
        cls,
        definition: HypothesisDefinition,
        *,
        claim_hash: str,
        permitted_claim_hashes: frozenset[str],
        relation_type: EvidenceHypothesisRelationType,
        relation_rule_id: str,
        relation_rule_version: str,
    ) -> EvidenceHypothesisRelationRecord:
        _sha256(claim_hash, "claim_hash")
        if claim_hash not in permitted_claim_hashes:
            raise ValueError("claim_hash is outside permitted lineage")
        if type(relation_type) is not EvidenceHypothesisRelationType:
            raise TypeError("relation_type must be EvidenceHypothesisRelationType")
        _non_empty(relation_rule_id, "relation_rule_id")
        _non_empty(relation_rule_version, "relation_rule_version")

        canonical_payload: dict[str, Any] = {
            "claim_hash": claim_hash,
            "hypothesis_definition_hash": definition.definition_hash,
            "hypothesis_id": definition.hypothesis_id,
            "relation_contract_version": CONTRACT_VERSION,
            "relation_rule_id": relation_rule_id,
            "relation_rule_version": relation_rule_version,
            "relation_type": relation_type.value,
        }
        record = object.__new__(cls)
        object.__setattr__(record, "hypothesis_id", definition.hypothesis_id)
        object.__setattr__(
            record,
            "hypothesis_definition_hash",
            definition.definition_hash,
        )
        object.__setattr__(record, "claim_hash", claim_hash)
        object.__setattr__(record, "relation_type", relation_type)
        object.__setattr__(record, "relation_rule_id", relation_rule_id)
        object.__setattr__(record, "relation_rule_version", relation_rule_version)
        object.__setattr__(record, "relation_contract_version", CONTRACT_VERSION)
        object.__setattr__(record, "record_hash", sha256_payload(canonical_payload))
        record._validate()
        return record

    def _validate(self) -> None:
        _sha256(self.hypothesis_id, "hypothesis_id")
        _sha256(self.hypothesis_definition_hash, "hypothesis_definition_hash")
        _sha256(self.claim_hash, "claim_hash")
        if self.hypothesis_id != self.hypothesis_definition_hash:
            raise ValueError("hypothesis identity must match definition hash")
        if self.relation_contract_version != CONTRACT_VERSION:
            raise ValueError("relation_contract_version is invalid")
        _sha256(self.record_hash, "record_hash")
        if self.record_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("record_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which record_hash is derived."""
        return {
            "claim_hash": self.claim_hash,
            "hypothesis_definition_hash": self.hypothesis_definition_hash,
            "hypothesis_id": self.hypothesis_id,
            "relation_contract_version": self.relation_contract_version,
            "relation_rule_id": self.relation_rule_id,
            "relation_rule_version": self.relation_rule_version,
            "relation_type": self.relation_type.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical record payload with its content identity."""
        return {**self.canonical_payload(), "record_hash": self.record_hash}


def build_evidence_hypothesis_relation_record(
    definition: HypothesisDefinition,
    *,
    claim_hash: str,
    permitted_claim_hashes: frozenset[str],
    relation_type: EvidenceHypothesisRelationType,
    relation_rule_id: str,
    relation_rule_version: str,
) -> EvidenceHypothesisRelationRecord:
    """Bind one permitted claim identity to one exact L5.1 definition."""
    if type(definition) is not HypothesisDefinition:
        raise TypeError("definition must be HypothesisDefinition")
    if type(permitted_claim_hashes) is not frozenset:
        raise TypeError("permitted_claim_hashes must be frozenset")
    if type(relation_type) is not EvidenceHypothesisRelationType:
        raise TypeError("relation_type must be EvidenceHypothesisRelationType")
    return EvidenceHypothesisRelationRecord._from_definition(
        definition,
        claim_hash=claim_hash,
        permitted_claim_hashes=permitted_claim_hashes,
        relation_type=relation_type,
        relation_rule_id=relation_rule_id,
        relation_rule_version=relation_rule_version,
    )
