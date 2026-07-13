"""Tests for the deterministic L7.0 admissibility decision request contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.admissibility import (
    AdmissibilityDecisionRequest,
    build_admissibility_decision_request,
)
from mh370_inverse_inference.comparative.result import ComparativeAssessmentResult
from mh370_inverse_inference.comparative.trace import ComparativeAssessmentTrace
from mh370_inverse_inference.engine.hashing import sha256_payload

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _result(result_hash: str, request_hash: str) -> ComparativeAssessmentResult:
    result = object.__new__(ComparativeAssessmentResult)
    object.__setattr__(result, "result_hash", result_hash)
    object.__setattr__(result, "comparative_request_hash", request_hash)
    return result


def _trace(
    trace_hash: str,
    result_hash: str,
    request_hash: str,
) -> ComparativeAssessmentTrace:
    trace = object.__new__(ComparativeAssessmentTrace)
    object.__setattr__(trace, "trace_hash", trace_hash)
    object.__setattr__(trace, "comparative_result_hash", result_hash)
    object.__setattr__(trace, "comparative_request_hash", request_hash)
    return trace


def test_request_is_deterministic_and_content_addressed() -> None:
    results = (_result(HASH_A, HASH_C), _result(HASH_B, HASH_D))
    traces = (_trace(HASH_C, HASH_A, HASH_C), _trace(HASH_D, HASH_B, HASH_D))

    first = build_admissibility_decision_request(
        results,
        traces,
        admissibility_policy_version="admissibility-policy-v1",
    )
    second = build_admissibility_decision_request(
        results,
        traces,
        admissibility_policy_version="admissibility-policy-v1",
    )

    assert first == second
    assert first.ordered_comparative_result_hashes == (HASH_A, HASH_B)
    assert first.ordered_comparative_trace_hashes == (HASH_C, HASH_D)
    assert first.request_hash == sha256_payload(first.canonical_payload())
    assert first.admissibility_request_contract_version == "L7.0"


def test_request_is_frozen_and_constructor_is_disabled() -> None:
    request = build_admissibility_decision_request(
        (_result(HASH_A, HASH_C),),
        (_trace(HASH_B, HASH_A, HASH_C),),
        admissibility_policy_version="admissibility-policy-v1",
    )
    request_type: Any = AdmissibilityDecisionRequest

    with pytest.raises(FrozenInstanceError):
        request.request_hash = HASH_D  # type: ignore[misc]

    with pytest.raises(TypeError):
        request_type(
            ordered_comparative_result_hashes=(HASH_A,),
            ordered_comparative_trace_hashes=(HASH_B,),
            admissibility_policy_version="admissibility-policy-v1",
            admissibility_request_contract_version="L7.0",
            request_hash=HASH_C,
        )


def test_empty_duplicate_and_mismatched_lineage_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one comparative result"):
        build_admissibility_decision_request(
            (),
            (),
            admissibility_policy_version="admissibility-policy-v1",
        )

    result = _result(HASH_A, HASH_C)
    trace = _trace(HASH_B, HASH_A, HASH_C)
    with pytest.raises(ValueError, match="duplicate result hashes"):
        build_admissibility_decision_request(
            (result, result),
            (trace, _trace(HASH_D, HASH_A, HASH_C)),
            admissibility_policy_version="admissibility-policy-v1",
        )

    with pytest.raises(ValueError, match="paired comparative result"):
        build_admissibility_decision_request(
            (result,),
            (_trace(HASH_B, HASH_D, HASH_C),),
            admissibility_policy_version="admissibility-policy-v1",
        )

    with pytest.raises(ValueError, match="comparative request lineage"):
        build_admissibility_decision_request(
            (result,),
            (_trace(HASH_B, HASH_A, HASH_D),),
            admissibility_policy_version="admissibility-policy-v1",
        )


def test_order_changes_request_identity() -> None:
    result_a = _result(HASH_A, HASH_C)
    result_b = _result(HASH_B, HASH_D)
    trace_a = _trace(HASH_C, HASH_A, HASH_C)
    trace_b = _trace(HASH_D, HASH_B, HASH_D)

    forward = build_admissibility_decision_request(
        (result_a, result_b),
        (trace_a, trace_b),
        admissibility_policy_version="admissibility-policy-v1",
    )
    reverse = build_admissibility_decision_request(
        (result_b, result_a),
        (trace_b, trace_a),
        admissibility_policy_version="admissibility-policy-v1",
    )

    assert forward.request_hash != reverse.request_hash


def test_payload_contains_only_contract_fields() -> None:
    request = build_admissibility_decision_request(
        (_result(HASH_A, HASH_C),),
        (_trace(HASH_B, HASH_A, HASH_C),),
        admissibility_policy_version="admissibility-policy-v1",
    )

    assert set(request.to_payload()) == {
        "admissibility_policy_version",
        "admissibility_request_contract_version",
        "ordered_comparative_result_hashes",
        "ordered_comparative_trace_hashes",
        "request_hash",
    }


def test_request_module_excludes_prohibited_dependencies() -> None:
    module_path = Path("src/mh370_inverse_inference/admissibility/request.py")
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
