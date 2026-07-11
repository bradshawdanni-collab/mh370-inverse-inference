"""Tests for deterministic L2.2 evidence validation."""

from dataclasses import replace

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.engine.trace import TraceStatus
from mh370_inverse_inference.evidence.assembly import assemble_evidence
from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyRequest,
    EvidenceAssemblyResult,
    EvidenceProvenanceLink,
)
from mh370_inverse_inference.evidence.validation import validate_evidence
from mh370_inverse_inference.evidence.validation_models import (
    EvidenceValidationReason,
    EvidenceValidationRequest,
    EvidenceValidationStatus,
)
from mh370_inverse_inference.evidence.validation_trace_adapter import (
    validation_result_to_trace,
)
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


def _assembled_result() -> EvidenceAssemblyResult:
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
    admission = ObservationAdmissionResult(
        status=AdmissionStatus.ADMITTED,
        reason_codes=(AdmissionReason.OK,),
        observation=observation,
        source=source,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        admission_policy_version="admission-1.0.0",
    )
    link = EvidenceProvenanceLink(
        link_index=0,
        subject_id="obs-001",
        predicate="derived-from",
        object_id="src-001",
        subject_hash=HASH_B,
        object_hash=HASH_A,
        source_reference="urn:observation:001",
    )
    request = EvidenceAssemblyRequest(
        admission_result=admission,
        provenance_chain=(link,),
        evidence_id="evidence-001",
        expected_model_version="observation-1.0.0",
        expected_contract_version="L2.1",
        assembly_policy_version="assembly-1.0.0",
    )
    return assemble_evidence(request)


def _validation_request(
    assembly: EvidenceAssemblyResult | None = None,
) -> EvidenceValidationRequest:
    result = _assembled_result() if assembly is None else assembly
    assert result.evidence_record is not None
    return EvidenceValidationRequest(
        assembly_result=result,
        expected_evidence_hash=sha256_payload(result.evidence_record.to_payload()),
        expected_contract_version="L2.2",
        validation_policy_version="validation-1.0.0",
    )


def test_valid_package_passes_deterministically() -> None:
    request = _validation_request()

    first = validate_evidence(request)
    second = validate_evidence(request)

    assert first == second
    assert first.status is EvidenceValidationStatus.VALID
    assert first.reason_codes == (EvidenceValidationReason.OK,)


def test_frozen_identity_hash_mismatch_fails_closed() -> None:
    request = replace(_validation_request(), expected_evidence_hash=HASH_C)

    result = validate_evidence(request)

    assert result.status is EvidenceValidationStatus.REJECTED
    assert result.reason_codes == (EvidenceValidationReason.EVIDENCE_HASH_MISMATCH,)


def test_observation_identity_mismatch_is_rejected() -> None:
    assembly = _assembled_result()
    assert assembly.evidence_record is not None
    altered_record = replace(assembly.evidence_record, observation_id="obs-altered")
    altered_assembly = replace(assembly, evidence_record=altered_record)

    result = validate_evidence(_validation_request(altered_assembly))

    assert EvidenceValidationReason.OBSERVATION_IDENTITY_MISMATCH in result.reason_codes
    assert EvidenceValidationReason.PROVENANCE_HASH_DISCONTINUITY in result.reason_codes


def test_provenance_hash_discontinuity_is_rejected() -> None:
    assembly = _assembled_result()
    assert assembly.evidence_record is not None
    link = replace(assembly.evidence_record.provenance_chain[0], subject_hash=HASH_C)
    altered_record = replace(assembly.evidence_record, provenance_chain=(link,))
    altered_assembly = replace(assembly, evidence_record=altered_record)

    result = validate_evidence(_validation_request(altered_assembly))

    assert result.status is EvidenceValidationStatus.REJECTED
    assert EvidenceValidationReason.PROVENANCE_HASH_DISCONTINUITY in result.reason_codes


def test_input_objects_remain_unchanged() -> None:
    request = _validation_request()
    before = request.to_payload()

    validate_evidence(request)

    assert request.to_payload() == before


def test_validation_result_maps_to_shared_trace_contract() -> None:
    result = validate_evidence(_validation_request())

    trace = validation_result_to_trace(result, stage_index=2)

    assert trace.stage_id == "L2.2-evidence-validation"
    assert trace.status is TraceStatus.OK
    assert trace.input_hash == result.input_hash
    assert trace.output_hash == result.output_hash
