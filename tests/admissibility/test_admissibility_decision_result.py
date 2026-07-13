"""Tests for the deterministic L7.2 admissibility decision result contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.admissibility import (
    AdmissibilityDecisionReason,
    AdmissibilityDecisionResult,
    AdmissibilityDecisionStatus,
    build_admissibility_decision_result,
)
from mh370_inverse_inference.admissibility.record import AdmissibilityDecisionRecord
from mh370_inverse_inference.admissibility.request import AdmissibilityDecisionRequest
from mh370_inverse_inference.engine.hashing import sha256_payload

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _request() -> AdmissibilityDecisionRequest:
    request = object.__new__(AdmissibilityDecisionRequest)
    object.__setattr__(request, "request_hash", HASH_A)
    return request


def _record(record_hash: str) -> AdmissibilityDecisionRecord:
    record = object.__new__(AdmissibilityDecisionRecord)
    object.__setattr__(record, "admissibility_request_hash", HASH_A)
    object.__setattr__(record, "record_hash", record_hash)
    return record


def test_result_is_deterministic_and_content_addressed() -> None:
    request = _request()
    records = (_record(HASH_B), _record(HASH_C))

    first = build_admissibility_decision_result(
        request,
        records=records,
        status=AdmissibilityDecisionStatus.COMPLETED,
        reason_codes=(AdmissibilityDecisionReason.OK,),
    )
    second = build_admissibility_decision_result(
        request,
        records=records,
        status=AdmissibilityDecisionStatus.COMPLETED,
        reason_codes=(AdmissibilityDecisionReason.OK,),
    )

    assert first == second
    assert first.admissibility_request_hash == request.request_hash
    assert first.ordered_record_hashes == (HASH_B, HASH_C)
    assert first.result_hash == sha256_payload(first.canonical_payload())
    assert first.admissibility_result_contract_version == "L7.2"


def test_result_is_frozen_and_constructor_is_disabled() -> None:
    result = build_admissibility_decision_result(
        _request(),
        records=(_record(HASH_B),),
        status=AdmissibilityDecisionStatus.COMPLETED,
        reason_codes=(AdmissibilityDecisionReason.OK,),
    )
    result_type: Any = AdmissibilityDecisionResult

    with pytest.raises(FrozenInstanceError):
        result.result_hash = HASH_C  # type: ignore[misc]

    with pytest.raises(TypeError):
        result_type(
            admissibility_request_hash=HASH_A,
            ordered_record_hashes=(HASH_B,),
            status=AdmissibilityDecisionStatus.COMPLETED,
            reason_codes=(AdmissibilityDecisionReason.OK,),
            admissibility_result_contract_version="L7.2",
            result_hash=HASH_C,
        )


def test_wrong_lineage_duplicates_and_empty_reasons_are_rejected() -> None:
    request = _request()
    wrong_record = _record(HASH_B)
    object.__setattr__(wrong_record, "admissibility_request_hash", HASH_C)

    with pytest.raises(ValueError, match="supplied admissibility request"):
        build_admissibility_decision_result(
            request,
            records=(wrong_record,),
            status=AdmissibilityDecisionStatus.REJECTED,
            reason_codes=(AdmissibilityDecisionReason.POLICY_REJECTED,),
        )

    record = _record(HASH_B)
    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_admissibility_decision_result(
            request,
            records=(record, record),
            status=AdmissibilityDecisionStatus.COMPLETED,
            reason_codes=(AdmissibilityDecisionReason.OK,),
        )

    with pytest.raises(ValueError, match="reason_codes cannot be empty"):
        build_admissibility_decision_result(
            request,
            records=(record,),
            status=AdmissibilityDecisionStatus.INSUFFICIENT_BASIS,
            reason_codes=(),
        )


def test_payload_contains_only_contract_fields() -> None:
    result = build_admissibility_decision_result(
        _request(),
        records=(_record(HASH_B),),
        status=AdmissibilityDecisionStatus.CONSTRAINT_VIOLATION,
        reason_codes=(AdmissibilityDecisionReason.CONSTRAINT_VIOLATION,),
    )

    assert set(result.to_payload()) == {
        "admissibility_request_hash",
        "admissibility_result_contract_version",
        "ordered_record_hashes",
        "reason_codes",
        "result_hash",
        "status",
    }


def test_result_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/admissibility/result.py")
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
        "execute",
    )

    for token in forbidden:
        assert token not in source
