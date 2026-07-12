"""Immutable deterministic L5.1 hypothesis definition contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L5.1"


class HypothesisType(StrEnum):
    """Neutral structural classifications for hypothesis definitions."""

    DESCRIPTIVE = "DESCRIPTIVE"
    RELATIONAL = "RELATIONAL"
    CONSTRAINT = "CONSTRAINT"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


@dataclass(frozen=True, slots=True, init=False)
class HypothesisDefinition:
    """Content-addressed neutral hypothesis definition."""

    hypothesis_id: str
    hypothesis_schema_version: str
    hypothesis_type: HypothesisType
    statement: str
    ordered_assumption_ids: tuple[str, ...]
    definition_hash: str

    @classmethod
    def _from_content(
        cls,
        *,
        hypothesis_schema_version: str,
        hypothesis_type: HypothesisType,
        statement: str,
        ordered_assumption_ids: tuple[str, ...],
    ) -> HypothesisDefinition:
        _non_empty(hypothesis_schema_version, "hypothesis_schema_version")
        _non_empty(statement, "statement")
        if type(hypothesis_type) is not HypothesisType:
            raise TypeError("hypothesis_type must be HypothesisType")
        for assumption_id in ordered_assumption_ids:
            _non_empty(assumption_id, "ordered_assumption_ids item")
        if len(set(ordered_assumption_ids)) != len(ordered_assumption_ids):
            raise ValueError("ordered_assumption_ids cannot contain duplicates")

        canonical_payload: dict[str, Any] = {
            "hypothesis_schema_version": hypothesis_schema_version,
            "hypothesis_type": hypothesis_type.value,
            "ordered_assumption_ids": list(ordered_assumption_ids),
            "statement": statement,
        }
        definition_hash = sha256_payload(canonical_payload)
        definition = object.__new__(cls)
        object.__setattr__(definition, "hypothesis_id", definition_hash)
        object.__setattr__(
            definition,
            "hypothesis_schema_version",
            hypothesis_schema_version,
        )
        object.__setattr__(definition, "hypothesis_type", hypothesis_type)
        object.__setattr__(definition, "statement", statement)
        object.__setattr__(
            definition,
            "ordered_assumption_ids",
            ordered_assumption_ids,
        )
        object.__setattr__(definition, "definition_hash", definition_hash)
        definition._validate()
        return definition

    def _validate(self) -> None:
        if self.hypothesis_id != self.definition_hash:
            raise ValueError("hypothesis_id must equal definition_hash")
        if self.definition_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("definition_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which definition_hash is derived."""
        return {
            "hypothesis_schema_version": self.hypothesis_schema_version,
            "hypothesis_type": self.hypothesis_type.value,
            "ordered_assumption_ids": list(self.ordered_assumption_ids),
            "statement": self.statement,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical definition payload with its identities."""
        return {
            **self.canonical_payload(),
            "definition_hash": self.definition_hash,
            "hypothesis_id": self.hypothesis_id,
        }


def build_hypothesis_definition(
    *,
    hypothesis_schema_version: str,
    hypothesis_type: HypothesisType,
    statement: str,
    ordered_assumption_ids: tuple[str, ...],
) -> HypothesisDefinition:
    """Seal neutral hypothesis content into a deterministic L5.1 definition."""
    if type(hypothesis_type) is not HypothesisType:
        raise TypeError("hypothesis_type must be HypothesisType")
    return HypothesisDefinition._from_content(
        hypothesis_schema_version=hypothesis_schema_version,
        hypothesis_type=hypothesis_type,
        statement=statement,
        ordered_assumption_ids=ordered_assumption_ids,
    )
