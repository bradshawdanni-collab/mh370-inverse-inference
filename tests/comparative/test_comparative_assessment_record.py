"""Tests for the deterministic L6.1 comparative assessment record contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.comparative import (
    ComparativeAssessmentRecord,
    ComparativeAssessmentRelation,
    ComparativeAssessmentRequest,
    build_comparative_assessment_record,
)
from mh370_inverse_inference.engine.hashing import sha256_payload

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _request() -> ComparativeAssessmentRequest:
    request = object.__new__(ComparativeAssessmentRequest)
    object.__setattr__(request, "request_hash", HASH_A)
    return request


def test_record_is_deterministic_and_content_addressed() -> None:
    request = _request()
    permitted = frozenset((HASH_B, HASH_C))

    first = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_B,
        right_hypothesis_id=HASH_C,
        permitted_hypothesis_ids=permitted,
        relation=ComparativeAssessmentRelation.DIFFERENT_DISPOSITION,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )
    second = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_B,
        right_hypothesis_id=HASH_C,
        permitted_hypothesis_ids=permitted,
        relation=ComparativeAssessmentRelation.DIFFERENT_DISPOSITION,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )

    assert first == second
    assert first.record_hash == sha256_payload(first.canonical_payload())
    assert first.comparative_request_hash == request.request_hash
    assert first.left_hypothesis_id == HASH_B
    assert first.right_hypothesis_id == HASH_C
    assert first.comparative_record_contract_version == "L6.1"


def test_record_is_frozen_and_constructor_is_disabled() -> None:
    request = _request()
    record = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_B,
        right_hypothesis_id=HASH_C,
        permitted_hypothesis_ids=frozenset((HASH_B, HASH_C)),
        relation=ComparativeAssessmentRelation.SAME_DISPOSITION,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )
    record_type: Any = ComparativeAssessmentRecord

    with pytest.raises(FrozenInstanceError):
        record.record_hash = HASH_A  # type: ignore[misc]

    with pytest.raises(TypeError):
        record_type(
            comparative_request_hash=HASH_A,
            left_hypothesis_id=HASH_B,
            right_hypothesis_id=HASH_C,
            relation=ComparativeAssessmentRelation.SAME_DISPOSITION,
            comparison_rule_id="COMPARE-001",
            comparison_rule_version="1.0.0",
            comparative_record_contract_version="L6.1",
            record_hash=HASH_A,
        )


def test_wrong_authority_self_comparison_and_lineage_are_rejected() -> None:
    request = _request()
    builder: Any = build_comparative_assessment_record

    with pytest.raises(TypeError):
        builder(
            {"request_hash": HASH_A},
            left_hypothesis_id=HASH_B,
            right_hypothesis_id=HASH_C,
            permitted_hypothesis_ids=frozenset((HASH_B, HASH_C)),
            relation=ComparativeAssessmentRelation.INDETERMINATE,
            comparison_rule_id="COMPARE-001",
            comparison_rule_version="1.0.0",
        )

    with pytest.raises(ValueError, match="cannot be compared with itself"):
        build_comparative_assessment_record(
            request,
            left_hypothesis_id=HASH_B,
            right_hypothesis_id=HASH_B,
            permitted_hypothesis_ids=frozenset((HASH_B, HASH_C)),
            relation=ComparativeAssessmentRelation.INDETERMINATE,
            comparison_rule_id="COMPARE-001",
            comparison_rule_version="1.0.0",
        )

    with pytest.raises(ValueError, match="outside permitted comparison lineage"):
        build_comparative_assessment_record(
            request,
            left_hypothesis_id=HASH_B,
            right_hypothesis_id=HASH_C,
            permitted_hypothesis_ids=frozenset((HASH_B,)),
            relation=ComparativeAssessmentRelation.INDETERMINATE,
            comparison_rule_id="COMPARE-001",
            comparison_rule_version="1.0.0",
        )


def test_pair_order_changes_record_identity() -> None:
    request = _request()
    permitted = frozenset((HASH_B, HASH_C))
    left_right = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_B,
        right_hypothesis_id=HASH_C,
        permitted_hypothesis_ids=permitted,
        relation=ComparativeAssessmentRelation.SAME_DISPOSITION,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )
    right_left = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_C,
        right_hypothesis_id=HASH_B,
        permitted_hypothesis_ids=permitted,
        relation=ComparativeAssessmentRelation.SAME_DISPOSITION,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )

    assert left_right.record_hash != right_left.record_hash


def test_payload_contains_only_contract_fields() -> None:
    request = _request()
    record = build_comparative_assessment_record(
        request,
        left_hypothesis_id=HASH_B,
        right_hypothesis_id=HASH_C,
        permitted_hypothesis_ids=frozenset((HASH_B, HASH_C)),
        relation=ComparativeAssessmentRelation.INDETERMINATE,
        comparison_rule_id="COMPARE-001",
        comparison_rule_version="1.0.0",
    )

    assert set(record.to_payload()) == {
        "comparative_record_contract_version",
        "comparative_request_hash",
        "comparison_rule_id",
        "comparison_rule_version",
        "left_hypothesis_id",
        "record_hash",
        "relation",
        "right_hypothesis_id",
    }


def test_record_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/comparative/record.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "datetime",
        "uuid",
        "random",
        "requests",
        "socket",
        "probability",
        "confidence",
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
