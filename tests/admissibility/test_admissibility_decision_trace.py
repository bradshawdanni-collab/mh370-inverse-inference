"""Tests for the deterministic L7.3 admissibility decision trace contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.admissibility import (
    AdmissibilityDecisionTrace,
    build_admissibility_decision_trace,
)
from mh370_inverse_inference.admissibility.record import AdmissibilityDecisionRecord
from mh370_inverse_inference.admissibility.result import AdmissibilityDecisionResult
from mh370_inverse_inference.engine.hashing import sha256_payload

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _result() -> AdmissibilityDecisionResult:
    result = object.__new__(AdmissibilityDecisionResult)
    object.__setattr__(result, "result_hash", HASH_A)
    object.__setattr__(result, "admissibility_request_hash", HASH_B)
    object.__setattr__(result, "ordered_record_hashes", (HASH_C, HASH_D))
    return result


def _record(record_hash: str) -> AdmissibilityDecisionRecord:
    record = object.__new__(AdmissibilityDecisionRecord)
    object.__setattr__(record, "admissibility_request_hash", HASH_B)
    object.__setattr__(record, "record_hash", record_hash)
    return record


def test_trace_is_deterministic_and_content_addressed() -> None:
    result = _result()
    records = (_record(HASH_C), _record(HASH_D))

    first = build_admissibility_decision_trace(result, records=records)
    second = build_admissibility_decision_trace(result, records=records)

    assert first == second
    assert first.admissibility_result_hash == HASH_A
    assert first.admissibility_request_hash == HASH_B
    assert first.ordered_record_hashes == (HASH_C, HASH_D)
    assert first.admissibility_trace_contract_version == "L7.3"
    assert first.trace_hash == sha256_payload(first.canonical_payload())


def test_trace_is_frozen_and_constructor_is_disabled() -> None:
    trace = build_admissibility_decision_trace(
        _result(),
        records=(_record(HASH_C), _record(HASH_D)),
    )
    trace_type: Any = AdmissibilityDecisionTrace

    with pytest.raises(FrozenInstanceError):
        trace.trace_hash = HASH_B  # type: ignore[misc]

    with pytest.raises(TypeError):
        trace_type(
            admissibility_result_hash=HASH_A,
            admissibility_request_hash=HASH_B,
            ordered_record_hashes=(HASH_C, HASH_D),
            admissibility_trace_contract_version="L7.3",
            trace_hash=HASH_A,
        )


def test_wrong_lineage_order_and_duplicates_are_rejected() -> None:
    result = _result()
    wrong = _record(HASH_C)
    object.__setattr__(wrong, "admissibility_request_hash", HASH_A)

    with pytest.raises(ValueError, match="result admissibility request"):
        build_admissibility_decision_trace(
            result,
            records=(wrong, _record(HASH_D)),
        )

    with pytest.raises(ValueError, match="preserve admissibility-result order"):
        build_admissibility_decision_trace(
            result,
            records=(_record(HASH_D), _record(HASH_C)),
        )

    duplicate_result = _result()
    object.__setattr__(duplicate_result, "ordered_record_hashes", (HASH_C, HASH_C))
    record = _record(HASH_C)
    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_admissibility_decision_trace(
            duplicate_result,
            records=(record, record),
        )


def test_payload_contains_only_contract_fields() -> None:
    trace = build_admissibility_decision_trace(
        _result(),
        records=(_record(HASH_C), _record(HASH_D)),
    )

    assert set(trace.to_payload()) == {
        "admissibility_request_hash",
        "admissibility_result_hash",
        "admissibility_trace_contract_version",
        "ordered_record_hashes",
        "trace_hash",
    }


def test_trace_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/admissibility/trace.py")
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
    )

    for token in forbidden:
        assert token not in source
