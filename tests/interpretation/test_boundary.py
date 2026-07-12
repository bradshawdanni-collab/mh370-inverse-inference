"""Boundary tests for deterministic L3.1 interpretation input."""

from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.consumption.models import (
    AcceptedEvidenceProjection,
    RegisteredEvidenceProjection,
)
from mh370_inverse_inference.evidence.registration_models import (
    RegisteredEvidenceRecord,
)
from mh370_inverse_inference.interpretation import build_interpretation_request

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def _accepted_projection() -> AcceptedEvidenceProjection:
    return AcceptedEvidenceProjection(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
    )


def _registered_record() -> RegisteredEvidenceRecord:
    return RegisteredEvidenceRecord(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
        validation_output_hash=HASH_D,
        validation_operation_hash=HASH_E,
    )


@pytest.mark.parametrize(
    "prohibited_input",
    [
        HASH_A,
        {"registry_evidence_id": HASH_A},
        _registered_record(),
        RegisteredEvidenceProjection.from_registered_record(_registered_record()),
    ],
)
def test_prohibited_inputs_are_rejected(prohibited_input: object) -> None:
    builder: Any = build_interpretation_request

    with pytest.raises(TypeError):
        builder(prohibited_input)


def test_interpretation_module_has_no_registry_or_nondeterministic_imports() -> None:
    package_root = (
        Path(__file__).parents[2] / "src" / "mh370_inverse_inference" / "interpretation"
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package_root.glob("*.py"))
    )

    prohibited_tokens = (
        "registration_models",
        "RegisteredEvidenceRecord",
        "RegisteredEvidenceProjection",
        "import random",
        "import time",
        "import uuid",
        "datetime.now",
        "os.environ",
        "open(",
        "requests.",
    )

    for token in prohibited_tokens:
        assert token not in source


def test_request_does_not_expose_raw_evidence_or_interpretation_fields() -> None:
    payload = build_interpretation_request(_accepted_projection()).to_payload()

    prohibited_fields = {
        "raw_evidence",
        "content",
        "payload",
        "likelihood",
        "probability",
        "rank",
        "score",
        "weight",
        "hypothesis",
        "trajectory",
    }

    assert prohibited_fields.isdisjoint(payload)
