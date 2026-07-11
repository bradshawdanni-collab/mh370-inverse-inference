"""Replay the frozen L2.1 evidence identity manifest."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from mh370_inverse_inference.engine.hashing import canonical_json_bytes
from mh370_inverse_inference.evidence.assembly import assemble_evidence
from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyRequest,
    EvidenceProvenanceLink,
)
from mh370_inverse_inference.evidence.trace_adapter import evidence_trace_record
from mh370_inverse_inference.observations.models import (
    AdmissionReason,
    AdmissionStatus,
    ObservationAdmissionResult,
    ObservationRecord,
    ObservationSource,
    ObservationType,
    ObservationUncertainty,
    ProvenanceStatus,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
MANIFEST = Path("tests/fixtures/evidence/identity_manifest.json")


def _admission(
    *,
    observation_id: str = "obs-001",
    observation_type: ObservationType = ObservationType.BTO,
    source_id: str = "src-001",
    measured_value: float = 12345.0,
    units: str = "us",
    standard_uncertainty: float = 20.0,
) -> ObservationAdmissionResult:
    suffix = observation_id.split("-")[-1]
    observation = ObservationRecord(
        observation_id=observation_id,
        observation_type=observation_type,
        timestamp_utc="2014-03-08T18:25:27Z",
        measured_value=measured_value,
        units=units,
        source_id=source_id,
        uncertainty=ObservationUncertainty(
            standard_uncertainty=standard_uncertainty,
            confidence_level=0.95,
            uncertainty_model="standard",
            units=units,
        ),
        model_version="observation-1.0.0",
    )
    source = ObservationSource(
        source_id=source_id,
        source_type="dataset",
        publisher="reference",
        reference_uri=f"urn:observation:{suffix}",
        retrieved_at_utc="2026-07-10T00:00:00Z",
        content_hash=HASH_A,
        provenance_status=ProvenanceStatus.VERIFIED,
    )
    return ObservationAdmissionResult(
        status=AdmissionStatus.ADMITTED,
        reason_codes=(AdmissionReason.OK,),
        observation=observation,
        source=source,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        admission_policy_version="admission-1.0.0",
    )


def _request(
    admission: ObservationAdmissionResult,
    *,
    evidence_id: str = "evidence-001",
    link_index: int = 0,
) -> EvidenceAssemblyRequest:
    source = admission.source
    assert source is not None
    link = EvidenceProvenanceLink(
        link_index=link_index,
        subject_id=admission.observation.observation_id,
        predicate="derived-from",
        object_id=source.source_id,
        subject_hash=admission.output_hash,
        object_hash=source.content_hash,
        source_reference=source.reference_uri,
    )
    return EvidenceAssemblyRequest(
        admission_result=admission,
        provenance_chain=(link,),
        evidence_id=evidence_id,
        expected_model_version="observation-1.0.0",
        expected_contract_version="L2.1",
        assembly_policy_version="assembly-1.0.0",
    )


def _cases() -> dict[str, EvidenceAssemblyRequest]:
    bto = _admission()
    bfo = _admission(
        observation_id="obs-002",
        observation_type=ObservationType.BFO,
        source_id="src-002",
        measured_value=42.5,
        units="Hz",
        standard_uncertainty=0.5,
    )
    rejected = replace(
        bto,
        status=AdmissionStatus.REJECTED,
        reason_codes=(AdmissionReason.INVALID_SCHEMA,),
    )
    quarantined = replace(
        bto,
        status=AdmissionStatus.QUARANTINED,
        reason_codes=(AdmissionReason.UNVERIFIED_PROVENANCE,),
    )
    return {
        "bto_evidence_001": _request(bto),
        "bfo_evidence_001": _request(bfo, evidence_id="evidence-002"),
        "rejected_source_001": _request(rejected),
        "quarantined_source_001": _request(quarantined),
        "invalid_provenance_001": _request(bto, link_index=1),
    }


@pytest.mark.parametrize("case_name", sorted(_cases()))
def test_frozen_evidence_fixture_replay(case_name: str) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    request = _cases()[case_name]
    request_before = canonical_json_bytes(request.to_payload())

    first = assemble_evidence(request)
    second = assemble_evidence(request)
    first_trace = evidence_trace_record(first, stage_index=4, duration_ms=1.0)
    second_trace = evidence_trace_record(second, stage_index=4, duration_ms=99.0)
    expected = manifest[case_name]

    assert first.input_hash == expected["input_hash"]
    assert first.output_hash == expected["output_hash"]
    assert first.status.value == expected["status"]
    assert first_trace.trace_hash == expected["trace_hash"]

    assert first.to_payload() == second.to_payload()
    assert first_trace.trace_hash == second_trace.trace_hash
    assert first_trace.metadata_json == second_trace.metadata_json
    assert canonical_json_bytes(request.to_payload()) == request_before

    metadata = json.loads(first_trace.metadata_json or "{}")
    assert first_trace.metadata_json == canonical_json_bytes(metadata).decode("utf-8")
    assert metadata["assembly_status"] == expected["status"]
    assert metadata["reason_codes"] == [reason.value for reason in first.reason_codes]

    assert first_trace.hypothesis_count is None
    assert first_trace.normalization_error is None
    assert first_trace.pre_normalization_mass is None
