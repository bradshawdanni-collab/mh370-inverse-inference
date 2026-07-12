"""Tests for the deterministic L5.1 hypothesis definition contract."""

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    HypothesisDefinition,
    HypothesisType,
    build_hypothesis_definition,
)


def _definition(
    *,
    hypothesis_type: HypothesisType = HypothesisType.DESCRIPTIVE,
    ordered_assumption_ids: tuple[str, ...] = ("ASSUMPTION-001",),
) -> HypothesisDefinition:
    return build_hypothesis_definition(
        hypothesis_schema_version="hypothesis-schema-1.0.0",
        hypothesis_type=hypothesis_type,
        statement="The admitted records satisfy a declared structural relation.",
        ordered_assumption_ids=ordered_assumption_ids,
    )


def test_definition_is_deterministic_and_content_addressed() -> None:
    first = _definition()
    second = _definition()

    assert first == second
    assert first.hypothesis_id == first.definition_hash
    assert first.definition_hash == sha256_payload(first.canonical_payload())


def test_assumption_order_is_part_of_definition_identity() -> None:
    first = _definition(ordered_assumption_ids=("ASSUMPTION-A", "ASSUMPTION-B"))
    second = _definition(ordered_assumption_ids=("ASSUMPTION-B", "ASSUMPTION-A"))

    assert first.definition_hash != second.definition_hash


def test_definition_supports_all_neutral_types() -> None:
    for hypothesis_type in HypothesisType:
        definition = _definition(hypothesis_type=hypothesis_type)
        assert definition.hypothesis_type is hypothesis_type


def test_blank_and_duplicate_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="hypothesis_schema_version cannot be blank"):
        build_hypothesis_definition(
            hypothesis_schema_version=" ",
            hypothesis_type=HypothesisType.DESCRIPTIVE,
            statement="Statement",
            ordered_assumption_ids=(),
        )

    with pytest.raises(ValueError, match="statement cannot be blank"):
        build_hypothesis_definition(
            hypothesis_schema_version="1.0.0",
            hypothesis_type=HypothesisType.DESCRIPTIVE,
            statement=" ",
            ordered_assumption_ids=(),
        )

    with pytest.raises(ValueError, match="cannot contain duplicates"):
        _definition(ordered_assumption_ids=("ASSUMPTION-A", "ASSUMPTION-A"))


def test_definition_is_frozen_and_public_constructor_is_disabled() -> None:
    definition = _definition()
    definition_type: Any = HypothesisDefinition

    with pytest.raises(FrozenInstanceError):
        definition.statement = "Changed"  # type: ignore[misc]

    with pytest.raises(TypeError):
        definition_type(
            hypothesis_id="a" * 64,
            hypothesis_schema_version="1.0.0",
            hypothesis_type=HypothesisType.DESCRIPTIVE,
            statement="Statement",
            ordered_assumption_ids=(),
            definition_hash="a" * 64,
        )


def test_definition_surface_contains_only_contract_fields() -> None:
    definition = _definition()

    assert tuple(field.name for field in fields(definition)) == (
        "hypothesis_id",
        "hypothesis_schema_version",
        "hypothesis_type",
        "statement",
        "ordered_assumption_ids",
        "definition_hash",
    )
    assert set(definition.to_payload()) == {
        "definition_hash",
        "hypothesis_id",
        "hypothesis_schema_version",
        "hypothesis_type",
        "ordered_assumption_ids",
        "statement",
    }


def test_definition_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/hypothesis/definition.py")
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
        "ranking",
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
