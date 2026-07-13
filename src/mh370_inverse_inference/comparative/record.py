"""Immutable deterministic L6.1 comparative assessment record contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.comparative.request import ComparativeAssessmentRequest
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L6.1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ComparativeAssessmentRelation(StrEnum):
    """Neutral structural relation asserted for one ordered hypothesis pair."""

    SAME_DISPOSITION = "SAME_DISPOSITION"
    DIFFERENT_DISPOSITION = "DIFFERENT_DISPOSITION"
    INDETERMINATE = "INDETERMINATE"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ComparativeAssessmentRecord:
    """Content-addressed structural comparison for one ordered pair."""

    comparative_request_hash: str
    left_hypothesis_id: str
    right_hypothesis_id: str
    relation: ComparativeAssessmentRelation
    comparison_rule_id: str
    comparison_rule_version: str
    comparative_record_contract_version: str
    record_hash: str

    @classmethod
    def _from_request(
        cls,
        request: ComparativeAssessmentRequest,
        *,
        left_hypothesis_id: str,
        right_hypothesis_id: str,
        relation: ComparativeAssessmentRelation,
        comparison_rule_id: str,
        comparison_rule_version: str,
    ) -> ComparativeAssessmentRecord:
        canonical_payload: dict[str, Any] = {
            "comparative_record_contract_version": CONTRACT_VERSION,
            "comparative_request_hash": request.request_hash,
            "comparison_rule_id": comparison_rule_id,
            "comparison_rule_version": comparison_rule_version,
            "left_hypothesis_id": left_hypothesis_id,
            "relation": relation.value,
            "right_hypothesis_id": right_hypothesis_id,
        }
        record = object.__new__(cls)
        object.__setattr__(record, "comparative_request_hash", request.request_hash)
        object.__setattr__(record, "left_hypothesis_id", left_hypothesis_id)
        object.__setattr__(record, "right_hypothesis_id", right_hypothesis_id)
        object.__setattr__(record, "relation", relation)
        object.__setattr__(record, "comparison_rule_id", comparison_rule_id)
        object.__setattr__(record, "comparison_rule_version", comparison_rule_version)
        object.__setattr__(
            record,
            "comparative_record_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(record, "record_hash", sha256_payload(canonical_payload))
        record._validate()
        return record

    def _validate(self) -> None:
        _sha256(self.comparative_request_hash, "comparative_request_hash")
        _sha256(self.left_hypothesis_id, "left_hypothesis_id")
        _sha256(self.right_hypothesis_id, "right_hypothesis_id")
        if self.left_hypothesis_id == self.right_hypothesis_id:
            raise ValueError("a hypothesis cannot be compared with itself")
        if type(self.relation) is not ComparativeAssessmentRelation:
            raise TypeError("relation must be ComparativeAssessmentRelation")
        _non_empty(self.comparison_rule_id, "comparison_rule_id")
        _non_empty(self.comparison_rule_version, "comparison_rule_version")
        if self.comparative_record_contract_version != CONTRACT_VERSION:
            raise ValueError("comparative_record_contract_version is invalid")
        _sha256(self.record_hash, "record_hash")
        if self.record_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("record_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which record_hash is derived."""
        return {
            "comparative_record_contract_version": (
                self.comparative_record_contract_version
            ),
            "comparative_request_hash": self.comparative_request_hash,
            "comparison_rule_id": self.comparison_rule_id,
            "comparison_rule_version": self.comparison_rule_version,
            "left_hypothesis_id": self.left_hypothesis_id,
            "relation": self.relation.value,
            "right_hypothesis_id": self.right_hypothesis_id,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical record payload with its content identity."""
        return {**self.canonical_payload(), "record_hash": self.record_hash}


def build_comparative_assessment_record(
    request: ComparativeAssessmentRequest,
    *,
    left_hypothesis_id: str,
    right_hypothesis_id: str,
    permitted_hypothesis_ids: frozenset[str],
    relation: ComparativeAssessmentRelation,
    comparison_rule_id: str,
    comparison_rule_version: str,
) -> ComparativeAssessmentRecord:
    """Bind one permitted ordered hypothesis pair to an exact L6.0 request."""
    if type(request) is not ComparativeAssessmentRequest:
        raise TypeError("request must be ComparativeAssessmentRequest")
    if type(permitted_hypothesis_ids) is not frozenset:
        raise TypeError("permitted_hypothesis_ids must be frozenset")
    _sha256(left_hypothesis_id, "left_hypothesis_id")
    _sha256(right_hypothesis_id, "right_hypothesis_id")
    if left_hypothesis_id == right_hypothesis_id:
        raise ValueError("a hypothesis cannot be compared with itself")
    if left_hypothesis_id not in permitted_hypothesis_ids:
        raise ValueError("left_hypothesis_id is outside permitted comparison lineage")
    if right_hypothesis_id not in permitted_hypothesis_ids:
        raise ValueError("right_hypothesis_id is outside permitted comparison lineage")
    if type(relation) is not ComparativeAssessmentRelation:
        raise TypeError("relation must be ComparativeAssessmentRelation")
    _non_empty(comparison_rule_id, "comparison_rule_id")
    _non_empty(comparison_rule_version, "comparison_rule_version")
    return ComparativeAssessmentRecord._from_request(
        request,
        left_hypothesis_id=left_hypothesis_id,
        right_hypothesis_id=right_hypothesis_id,
        relation=relation,
        comparison_rule_id=comparison_rule_id,
        comparison_rule_version=comparison_rule_version,
    )
