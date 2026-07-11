"""Frozen identity fixtures for L2.0 observation admission."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from mh370_inverse_inference.engine.hashing import canonical_json_bytes
from mh370_inverse_inference.observations.admission import admit_observation
from mh370_inverse_inference.observations.models import (
    ObservationAdmissionRequest,
    ObservationRecord,
    ObservationSource,
    ObservationType,
    ObservationUncertainty,
    ProvenanceStatus,
)
from mh370_inverse_inference.observations.trace_adapter import admission_trace_record

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "observations"
CASES = (
    "bto_admitted_001",
    "bfo_admitted_001",
    "invalid_non_finite_001",
    "quarantined_provenance_001",
)
FORBIDDEN_FIELDS = {
    "residual",
    "likelihood",
    "posterior",
    "trajectory",
    "drift",
    "endpoint",
}


def _load(name: str, suffix: str) -> dict[str, Any]:
    path = FIXTURE_DIR / f"{name}.{suffix}.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _request(payload: dict[str, Any]) -> ObservationAdmissionRequest:
    observation_payload = payload["observation"]
    source_payload = payload["source"]
    uncertainty_payload = observation_payload["uncertainty"]
    measured_value = observation_payload["measured_value"]
    if measured_value == "__NaN__":
        measured_value = math.nan

    uncertainty = ObservationUncertainty(
        standard_uncertainty=uncertainty_payload["standard_uncertainty"],
        confidence_level=uncertainty_payload["confidence_level"],
        uncertainty_model=uncertainty_payload["uncertainty_model"],
        units=uncertainty_payload["units"],
    )
    observation = ObservationRecord(
        observation_id=observation_payload["observation_id"],
        observation_type=ObservationType(observation_payload["observation_type"]),
        timestamp_utc=observation_payload["timestamp_utc"],
        measured_value=measured_value,
        units=observation_payload["units"],
        source_id=observation_payload["source_id"],
        uncertainty=uncertainty,
        model_version=observation_payload["model_version"],
        contract_version=observation_payload["contract_version"],
    )
    source = ObservationSource(
        source_id=source_payload["source_id"],
        source_type=source_payload["source_type"],
        publisher=source_payload["publisher"],
        reference_uri=source_payload["reference_uri"],
        retrieved_at_utc=source_payload["retrieved_at_utc"],
        content_hash=source_payload["content_hash"],
        provenance_status=ProvenanceStatus(source_payload["provenance_status"]),
    )
    return ObservationAdmissionRequest(
        observation=observation,
        source=source,
        expected_model_version=payload["expected_model_version"],
        expected_contract_version=payload["expected_contract_version"],
        admission_policy_version=payload["admission_policy_version"],
    )


def _identity_snapshot(request: ObservationAdmissionRequest) -> dict[str, Any]:
    result = admit_observation(request)
    trace = admission_trace_record(result, stage_index=4)
    return {
        "input_hash": result.input_hash,
        "op_signature_hash": result.op_signature_hash,
        "output_hash": result.output_hash,
        "reason_codes": [reason.value for reason in result.reason_codes],
        "status": result.status.value,
        "trace_hash": trace.trace_hash,
    }


def test_frozen_observation_identity_fixtures() -> None:
    for case in CASES:
        request = _request(_load(case, "input"))
        first = _identity_snapshot(request)
        second = _identity_snapshot(request)

        assert first == second
        assert first == _load(case, "expected")


def test_canonical_bytes_are_exact_across_replay() -> None:
    for case in CASES:
        request = _request(_load(case, "input"))
        first = admit_observation(request)
        second = admit_observation(request)

        assert canonical_json_bytes(first.to_payload()) == canonical_json_bytes(
            second.to_payload()
        )


def test_duration_does_not_change_identity_hashes() -> None:
    request = _request(_load("bto_admitted_001", "input"))
    result = admit_observation(request)
    first = admission_trace_record(result, stage_index=4, duration_ms=1.0)
    second = admission_trace_record(result, stage_index=4, duration_ms=2.0)

    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.op_signature_hash == second.op_signature_hash
    assert first.trace_hash == second.trace_hash


def test_source_and_request_are_not_mutated() -> None:
    request = _request(_load("bto_admitted_001", "input"))
    before = request.to_payload()

    admit_observation(request)

    assert request.to_payload() == before


def test_admission_contract_excludes_inference_fields() -> None:
    request = _request(_load("bto_admitted_001", "input"))
    result = admit_observation(request)
    serialized = canonical_json_bytes(result.to_payload()).decode("utf-8").lower()

    for field in FORBIDDEN_FIELDS:
        assert field not in serialized
