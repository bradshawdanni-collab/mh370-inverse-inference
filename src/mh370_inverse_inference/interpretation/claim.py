"""Deterministic L3.3 neutral derived claim contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L3.3"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class NeutralClaimType(StrEnum):
    """Allowlisted non-substantive claim categories."""

    SOURCE_PRESENT = "SOURCE_PRESENT"
    OBSERVATION_LINKED = "OBSERVATION_LINKED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    EVIDENCE_CONSUMED = "EVIDENCE_CONSUMED"
    RULE_APPLIED = "RULE_APPLIED"


class ClaimStatus(StrEnum):
    """Stable neutral claim outcomes."""

    ASSERTED = "ASSERTED"
    WITHHELD = "WITHHELD"
    INSUFFICIENT_SUPPORT = "INSUFFICIENT_SUPPORT"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class NeutralDerivedClaim:
    """Frozen, content-addressed structural claim with no inference semantics."""

    claim_id: str
    claim_type: NeutralClaimType
    statement: str
    supporting_evidence_ids: tuple[str, ...]
    interpretation_rule_id: str
    interpretation_rule_version: str
    claim_status: ClaimStatus
    claim_hash: str
    claim_contract_version: str

    @classmethod
    def _from_parts(
        cls,
        *,
        claim_type: NeutralClaimType,
        statement: str,
        supporting_evidence_ids: tuple[str, ...],
        interpretation_rule_id: str,
        interpretation_rule_version: str,
        claim_status: ClaimStatus,
    ) -> NeutralDerivedClaim:
        canonical_payload: dict[str, Any] = {
            "claim_contract_version": CONTRACT_VERSION,
            "claim_status": claim_status.value,
            "claim_type": claim_type.value,
            "interpretation_rule_id": interpretation_rule_id,
            "interpretation_rule_version": interpretation_rule_version,
            "statement": statement,
            "supporting_evidence_ids": list(supporting_evidence_ids),
        }
        claim_hash = sha256_payload(canonical_payload)
        claim = object.__new__(cls)
        object.__setattr__(claim, "claim_id", claim_hash)
        object.__setattr__(claim, "claim_type", claim_type)
        object.__setattr__(claim, "statement", statement)
        object.__setattr__(
            claim,
            "supporting_evidence_ids",
            supporting_evidence_ids,
        )
        object.__setattr__(claim, "interpretation_rule_id", interpretation_rule_id)
        object.__setattr__(
            claim,
            "interpretation_rule_version",
            interpretation_rule_version,
        )
        object.__setattr__(claim, "claim_status", claim_status)
        object.__setattr__(claim, "claim_hash", claim_hash)
        object.__setattr__(claim, "claim_contract_version", CONTRACT_VERSION)
        claim._validate()
        return claim

    def _validate(self) -> None:
        _sha256(self.claim_id, "claim_id")
        _sha256(self.claim_hash, "claim_hash")
        if self.claim_id != self.claim_hash:
            raise ValueError("claim_id must equal claim_hash")
        _non_empty(self.statement, "statement")
        _non_empty(self.interpretation_rule_id, "interpretation_rule_id")
        _non_empty(
            self.interpretation_rule_version,
            "interpretation_rule_version",
        )
        if not self.supporting_evidence_ids:
            raise ValueError("supporting_evidence_ids cannot be empty")
        for evidence_id in self.supporting_evidence_ids:
            _sha256(evidence_id, "supporting_evidence_ids item")
        if len(set(self.supporting_evidence_ids)) != len(
            self.supporting_evidence_ids
        ):
            raise ValueError("supporting_evidence_ids cannot contain duplicates")
        if self.claim_contract_version != CONTRACT_VERSION:
            raise ValueError(f"claim_contract_version must be {CONTRACT_VERSION}")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which claim_hash is derived."""
        return {
            "claim_contract_version": self.claim_contract_version,
            "claim_status": self.claim_status.value,
            "claim_type": self.claim_type.value,
            "interpretation_rule_id": self.interpretation_rule_id,
            "interpretation_rule_version": self.interpretation_rule_version,
            "statement": self.statement,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical claim payload with its content identity."""
        return {
            **self.canonical_payload(),
            "claim_hash": self.claim_hash,
            "claim_id": self.claim_id,
        }


def build_neutral_derived_claim(
    *,
    claim_type: NeutralClaimType,
    statement: str,
    supporting_evidence_ids: tuple[str, ...],
    permitted_evidence_ids: frozenset[str],
    interpretation_rule_id: str,
    interpretation_rule_version: str,
    claim_status: ClaimStatus,
) -> NeutralDerivedClaim:
    """Build one neutral claim constrained to explicitly permitted lineage."""
    if type(claim_type) is not NeutralClaimType:
        raise TypeError("claim_type must be NeutralClaimType")
    if type(claim_status) is not ClaimStatus:
        raise TypeError("claim_status must be ClaimStatus")
    if type(supporting_evidence_ids) is not tuple:
        raise TypeError("supporting_evidence_ids must be tuple[str, ...]")
    if type(permitted_evidence_ids) is not frozenset:
        raise TypeError("permitted_evidence_ids must be frozenset[str]")
    if not set(supporting_evidence_ids).issubset(permitted_evidence_ids):
        raise ValueError("supporting evidence is outside permitted lineage")
    return NeutralDerivedClaim._from_parts(
        claim_type=claim_type,
        statement=statement,
        supporting_evidence_ids=supporting_evidence_ids,
        interpretation_rule_id=interpretation_rule_id,
        interpretation_rule_version=interpretation_rule_version,
        claim_status=claim_status,
    )
