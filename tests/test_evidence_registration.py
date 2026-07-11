"""Tests for deterministic L2.3 evidence registration."""

from dataclasses import replace

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.engine.trace import TraceStatus
from mh370_inverse_inference.evidence.assembly import assemble_evidence
from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyRequest,
    EvidenceProvenanceLink,
)
from mh370_inverse_inference.evidence.registration import register_evidence
from mh370_inverse_inference.evidence.registration_models import (
    EvidenceRegistrationReason,
    EvidenceRegistrationRequest,
    EvidenceRegistrationStatus,
)
from mh370_inverse_inference.evidence.registration_trace_adapter import (
    registration_result_to_trace,
)
from mh370_inverse_inference.evidence.validation import validate_evidence
from mh370_inverse_inference.evidence.validation_models import (
    EvidenceValidationReason,
    EvidenceValidationRequest,
    EvidenceValidationStatus,
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


def _validation_result():
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
    assembly = assemble_evidence(
        EvidenceAssemblyRequest(
            admission_result=admission,
            provenance_chain=(link,),
            evidence_id="evidence-001",
            expected_model_version="observation-1.0.0",
            expected_contract_version="L2.1",
            assembly_policy_version="assembly-1.0.0",
        )
    )
    assert assembly.evidence_record is not None
    evidence_hash = sha256_payload(assembly.evidence_record.to_payload())
    return validate_evidence(
        EvidenceValidationRequest(
            assembly_result=assembly,
            expected_evidence_hash=evidence_hash,
            expected_contract_version="L2.2",
            validation_policy_version="validation-1.0.0",
        )
    )


def _registration_request(validation=None) -> EvidenceRegistrationRequest:
    result = _validation_result() if validation is None else validation
    record = result.assembly_result.evidence_record
    assert record is not None
    return EvidenceRegistrationRequest(
        validation_result=result,
        expected_evidence_hash=sha256_payload(record.to_payload()),
        expected_validation_hash=sha256_payload(result.to_payload()),
        expected_contract_version="L2.3",
        registry_policy_version="registry-1.0.0",
    )


def test_valid_evidence_registers_deterministically() -> None:
    request = _registration_request()

    first = register_evidence(request)
    second = register_evidence(request)

    assert first == second
    assert first.status is EvidenceRegistrationStatus.REGISTERED
    assert first.reason_codes == (EvidenceRegistrationReason.OK,)
    assert first.registered_record is not None


def test_registry_identity_matches_frozen_identity_payload() -> None:
    request = _registration_request()
    result = register_evidence(request)

    assert result.registered_record is not None
    record = request.validation_result.assembly_result.evidence_record
    assert record is not None
    expected_id = sha256_payload(
        {
            "evidence_record": record.to_payload(),
            "registration_contract_version": "L2.3",
            "validation_operation_hash": request.validation_result.op_signature_hash,
            "validation_output_hash": request.validation_result.output_hash,
        }
    )
    assert result.registered_record.registry_evidence_id == expected_id


def test_rejected_validation_cannot_register() -> None:
    validation = replace(
        _validation_result(),
        status=EvidenceValidationStatus.REJECTED,
        reason_codes=(EvidenceValidationReason.EVIDENCE_HASH_MISMATCH,),
    )
    request = _registration_request(validation)

    result = register_evidence(request)

    assert result.status is EvidenceRegistrationStatus.REJECTED
    assert result.registered_record is None
    assert result.reason_codes[0] is EvidenceRegistrationReason.VALIDATION_NOT_VALID


def test_validation_identity_mismatch_fails_closed() -> None:
    request = replace(_registration_request(), expected_validation_hash=HASH_C)

    result = register_evidence(request)

    assert result.status is EvidenceRegistrationStatus.REJECTED
    assert EvidenceRegistrationReason.VALIDATION_HASH_MISMATCH in result.reason_codes


def test_inconsistent_validation_proof_fails_closed() -> None:
    validation = replace(_validation_result(), output_hash=HASH_C)
    request = _registration_request(validation)

    result = register_evidence(request)

    assert result.status is EvidenceRegistrationStatus.REJECTED
    assert (
        EvidenceRegistrationReason.VALIDATION_RESULT_INCONSISTENT
        in result.reason_codes
    )


def test_registration_does_not_mutate_validation_artifacts() -> None:
    request = _registration_request()
    before = request.to_payload()

    register_evidence(request)

    assert request.to_payload() == before


def test_registration_result_maps_to_shared_trace_contract() -> None:
    result = register_evidence(_registration_request())

    trace = registration_result_to_trace(result, stage_index=3)

    assert trace.stage_id == "L2.3-evidence-registration"
    assert trace.status is TraceStatus.OK
    assert trace.record_count == 1
    assert trace.input_hash == result.input_hash
    assert trace.output_hash == result.output_hash
