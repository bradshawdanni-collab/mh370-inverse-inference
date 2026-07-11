"""Tests for L2.1 evidence mapping into the shared L10 trace contract."""

import json
from dataclasses import replace

from mh370_inverse_inference.engine.trace import TraceStatus
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


def _admission() -> ObservationAdmissionResult:
    observation = ObservationRecord(
        observation_id="obs-001",
        observation_type=ObservationType.BTO,
        timestamp_utc="2014-03-08T18:25:27Z",
        measured_value=12345.0,
        units="us",
        source_id="src-001",
        uncertainty=ObservationUncertainty(
            standard_uncertainty=20.0,
            confidence_level=0.95,
            uncertainty_model="standard",
            units="us",
        ),
        model_version="observation-1.0.0",
    )
    source = ObservationSource(
        source_id="src-001",
        source_type="dataset",
        publisher="reference",
        reference_uri="urn:observation:001",
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


def _request(admission: ObservationAdmissionResult) -> EvidenceAssemblyRequest:
    link = EvidenceProvenanceLink(
        link_index=0,
        subject_id="obs-001",
        predicate="derived-from",
        object_id="src-001",
        subject_hash=HASH_B,
        object_hash=HASH_A,
        source_reference="urn:observation:001",
    )
    return EvidenceAssemblyRequest(
        admission_result=admission,
        provenance_chain=(link,),
        evidence_id="evidence-001",
        expected_model_version="observation-1.0.0",
        expected_contract_version="L2.1",
        assembly_policy_version="assembly-1.0.0",
    )


def test_assembled_result_maps_to_ok_trace() -> None:
    result = assemble_evidence(_request(_admission()))
    trace = evidence_trace_record(result, stage_index=4, duration_ms=2.5)

    assert trace.stage_id == "observation_evidence_assembly"
    assert trace.stage_index == 4
    assert trace.status is TraceStatus.OK
    assert trace.record_count == 1
    assert trace.failure_kind is None
    assert trace.hypothesis_count is None
    assert trace.normalization_error is None
    assert trace.pre_normalization_mass is None

    metadata = json.loads(trace.metadata_json or "{}")
    assert metadata["evidence_id"] == "evidence-001"
    assert metadata["provenance_link_count"] == 1
    assert metadata["assembly_status"] == "ASSEMBLED"


def test_rejected_result_maps_to_failed_trace() -> None:
    rejected = replace(
        _admission(),
        status=AdmissionStatus.REJECTED,
        reason_codes=(AdmissionReason.INVALID_SCHEMA,),
    )
    result = assemble_evidence(_request(rejected))
    trace = evidence_trace_record(result, stage_index=4)

    assert trace.status is TraceStatus.FAILED
    assert trace.record_count == 0
    assert trace.failure_kind == "SOURCE_NOT_ADMITTED"


def test_duration_does_not_change_trace_identity() -> None:
    result = assemble_evidence(_request(_admission()))

    first = evidence_trace_record(result, stage_index=4, duration_ms=1.0)
    second = evidence_trace_record(result, stage_index=4, duration_ms=99.0)

    assert first.trace_hash == second.trace_hash
    assert first.input_hash == second.input_hash
    assert first.output_hash == second.output_hash
    assert first.op_signature_hash == second.op_signature_hash
