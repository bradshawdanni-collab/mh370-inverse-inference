"""Tests for immutable L2.1 evidence contracts."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyReason,
    EvidenceAssemblyRequest,
    EvidenceAssemblyResult,
    EvidenceAssemblyStatus,
    EvidenceProvenanceLink,
    EvidenceRecord,
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


def admission_result() -> ObservationAdmissionResult:
    uncertainty = ObservationUncertainty(
        standard_uncertainty=20.0,
        confidence_level=0.95,
        uncertainty_model="standard",
        units="us",
    )
    observation = ObservationRecord(
        observation_id="obs-001",
        observation_type=ObservationType.BTO,
        timestamp_utc="2014-03-08T18:25:27Z",
        measured_value=12345.0,
        units="us",
        source_id="src-001",
        uncertainty=uncertainty,
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


def provenance_link() -> EvidenceProvenanceLink:
    return EvidenceProvenanceLink(
        link_index=0,
        subject_id="obs-001",
        predicate="derived-from",
        object_id="src-001",
        subject_hash=HASH_B,
        object_hash=HASH_A,
        source_reference="urn:observation:001",
    )


def evidence_record() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="evidence-001",
        observation_id="obs-001",
        observation_type=ObservationType.BTO,
        observation_hash=HASH_B,
        source_id="src-001",
        source_hash=HASH_A,
        provenance_chain=(provenance_link(),),
        assembled_at_policy_version="assembly-1.0.0",
        model_version="evidence-1.0.0",
    )


def test_contracts_are_immutable() -> None:
    record = evidence_record()

    with pytest.raises(FrozenInstanceError):
        record.evidence_id = "changed"  # type: ignore[misc]


def test_provenance_payload_preserves_link_order() -> None:
    first = provenance_link()
    second = EvidenceProvenanceLink(
        link_index=1,
        subject_id="evidence-001",
        predicate="packages",
        object_id="obs-001",
        subject_hash=HASH_C,
        object_hash=HASH_B,
        source_reference="urn:evidence:001",
    )
    record = EvidenceRecord(
        evidence_id="evidence-001",
        observation_id="obs-001",
        observation_type=ObservationType.BTO,
        observation_hash=HASH_B,
        source_id="src-001",
        source_hash=HASH_A,
        provenance_chain=(first, second),
        assembled_at_policy_version="assembly-1.0.0",
        model_version="evidence-1.0.0",
    )

    payload = record.to_payload()
    assert [item["link_index"] for item in payload["provenance_chain"]] == [0, 1]


def test_request_payload_preserves_admission_identity() -> None:
    admission = admission_result()
    request = EvidenceAssemblyRequest(
        admission_result=admission,
        provenance_chain=(provenance_link(),),
        evidence_id="evidence-001",
        expected_model_version="evidence-1.0.0",
        expected_contract_version="L2.1",
        assembly_policy_version="assembly-1.0.0",
    )

    payload = request.to_payload()
    assert payload["admission_result"]["output_hash"] == admission.output_hash
    assert payload["admission_result"]["source"]["content_hash"] == HASH_A


def test_assembled_result_requires_evidence_record() -> None:
    admission = admission_result()

    with pytest.raises(ValueError, match="requires evidence_record"):
        EvidenceAssemblyResult(
            status=EvidenceAssemblyStatus.ASSEMBLED,
            reason_codes=(EvidenceAssemblyReason.OK,),
            evidence_record=None,
            admission_result=admission,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            assembly_policy_version="assembly-1.0.0",
        )


def test_rejected_result_cannot_include_evidence_record() -> None:
    admission = admission_result()

    with pytest.raises(ValueError, match="cannot include evidence_record"):
        EvidenceAssemblyResult(
            status=EvidenceAssemblyStatus.REJECTED,
            reason_codes=(EvidenceAssemblyReason.SOURCE_NOT_ADMITTED,),
            evidence_record=evidence_record(),
            admission_result=admission,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            assembly_policy_version="assembly-1.0.0",
        )
