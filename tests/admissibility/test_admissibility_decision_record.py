"""Tests for the deterministic L7.1 admissibility decision record contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.admissibility import (
    AdmissibilityDecisionRecord,
    AdmissibilityOutcome,
    build_admissibility_decision_record,
)
from mh370_inverse_inference.admissibility.request import AdmissibilityDecisionRequest
from mh370_inverse_inference.comparative.result import ComparativeAssessmentResult
from mh370_inverse_inference.engine.hashing import sha256_payload

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _request(*result_hashes: str) -> AdmissibilityDecisionRequest:
    request = object.__new__(AdmissibilityDecisionRequest)
    object.__setattr__(request, "request_hash", HASH_A)
    object.__setattr__(
        request,
        "ordered_comparative_result_hashes",
        tuple(result_hashes),
    )
    return request


def _result(result_hash: str) -> ComparativeAssessmentResult:
    result = object.__new__(ComparativeAssessmentResult)
    object.__setattr__(result, "result_hash", result_hash)
    return result


def test_record_is_deterministic_and_content_addressed() -> None:
    request = _request(HASH_B)
    result = _result(HASH_B)

    first = build_admissibility_decision_record(
        request,
        result,
        outcome=AdmissibilityOutcome.ADMISSIBLE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )
    second = build_admissibility_decision_record(
        request,
        result,
        outcome=AdmissibilityOutcome.ADMISSIBLE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )

    assert first == second
    assert first.admissibility_request_hash == request.request_hash
    assert first.comparative_result_hash == result.result_hash
    assert first.record_hash == sha256_payload(first.canonical_payload())
    assert first.admissibility_record_contract_version == "L7.1"


def test_record_is_frozen_and_constructor_is_disabled() -> None:
    record = build_admissibility_decision_record(
        _request(HASH_B),
        _result(HASH_B),
        outcome=AdmissibilityOutcome.INDETERMINATE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )
    record_type: Any = AdmissibilityDecisionRecord

    with pytest.raises(FrozenInstanceError):
        record.record_hash = HASH_C  # type: ignore[misc]

    with pytest.raises(TypeError):
        record_type(
            admissibility_request_hash=HASH_A,
            comparative_result_hash=HASH_B,
            outcome=AdmissibilityOutcome.ADMISSIBLE,
            decision_rule_id="structural-admissibility",
            decision_rule_version="1.0.0",
            admissibility_record_contract_version="L7.1",
            record_hash=HASH_C,
        )


def test_result_membership_and_rule_fields_are_enforced() -> None:
    request = _request(HASH_B)

    with pytest.raises(ValueError, match="outside the supplied admissibility request"):
        build_admissibility_decision_record(
            request,
            _result(HASH_C),
            outcome=AdmissibilityOutcome.INADMISSIBLE,
            decision_rule_id="structural-admissibility",
            decision_rule_version="1.0.0",
        )

    with pytest.raises(ValueError, match="decision_rule_id cannot be blank"):
        build_admissibility_decision_record(
            request,
            _result(HASH_B),
            outcome=AdmissibilityOutcome.CONSTRAINT_VIOLATION,
            decision_rule_id=" ",
            decision_rule_version="1.0.0",
        )

    with pytest.raises(ValueError, match="decision_rule_version cannot be blank"):
        build_admissibility_decision_record(
            request,
            _result(HASH_B),
            outcome=AdmissibilityOutcome.CONSTRAINT_VIOLATION,
            decision_rule_id="structural-admissibility",
            decision_rule_version=" ",
        )


def test_outcome_changes_record_identity() -> None:
    request = _request(HASH_B)
    result = _result(HASH_B)
    admissible = build_admissibility_decision_record(
        request,
        result,
        outcome=AdmissibilityOutcome.ADMISSIBLE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )
    inadmissible = build_admissibility_decision_record(
        request,
        result,
        outcome=AdmissibilityOutcome.INADMISSIBLE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )

    assert admissible.record_hash != inadmissible.record_hash


def test_payload_contains_only_contract_fields() -> None:
    record = build_admissibility_decision_record(
        _request(HASH_B),
        _result(HASH_B),
        outcome=AdmissibilityOutcome.INDETERMINATE,
        decision_rule_id="structural-admissibility",
        decision_rule_version="1.0.0",
    )

    assert set(record.to_payload()) == {
        "admissibility_record_contract_version",
        "admissibility_request_hash",
        "comparative_result_hash",
        "decision_rule_id",
        "decision_rule_version",
        "outcome",
        "record_hash",
    }


def test_record_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/admissibility/record.py")
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "datetime",
        "uuid",
        "random",
        "requests",
        "socket",
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
        "registry",
        "execute",
    )

    for token in forbidden:
        assert token not in source
