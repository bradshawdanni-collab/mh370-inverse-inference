"""Tests for the immutable L3.1 interpretation request value object."""

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation import (
    InterpretationRequest,
    build_interpretation_request,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _accepted_projection() -> AcceptedEvidenceProjection:
    return AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )


def test_request_is_deterministic_and_content_addressed() -> None:
    projection = _accepted_projection()

    first = build_interpretation_request(projection)
    second = build_interpretation_request(projection)

    assert first == second
    assert first.input_hash == sha256_payload(first.canonical_payload())
    assert first.interpretation_contract_version == "L3.1"


def test_request_preserves_only_permitted_lineage() -> None:
    projection = _accepted_projection()

    request = build_interpretation_request(projection)

    assert request.registry_evidence_id == projection.registry_evidence_id
    assert request.evidence_id == projection.evidence_id
    assert request.observation_id == projection.observation_id
    assert request.source_id == projection.source_id
    assert request.evidence_hash == projection.evidence_hash
    assert request.validation_hash == projection.validation_hash
    assert request.consumption_contract_version == "L3.0"
    assert set(request.to_payload()) == {
        "consumption_contract_version",
        "evidence_hash",
        "evidence_id",
        "input_hash",
        "interpretation_contract_version",
        "observation_id",
        "registry_evidence_id",
        "source_id",
        "validation_hash",
    }


def test_request_is_frozen() -> None:
    request = build_interpretation_request(_accepted_projection())

    with pytest.raises(FrozenInstanceError):
        request.evidence_id = "changed"  # type: ignore[misc]


def test_public_constructor_is_disabled() -> None:
    request_type: Any = InterpretationRequest

    with pytest.raises(TypeError):
        request_type(
            registry_evidence_id=HASH_A,
            evidence_id="evidence-001",
            observation_id="obs-001",
            source_id="src-001",
            evidence_hash=HASH_B,
            validation_hash=HASH_C,
            consumption_contract_version="L3.0",
            interpretation_contract_version="L3.1",
            input_hash=HASH_A,
        )
