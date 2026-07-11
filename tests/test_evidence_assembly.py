"""Tests for deterministic L2.1 evidence assembly."""

from dataclasses import replace

from mh370_inverse_inference.evidence.assembly import assemble_evidence
from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyReason,
    EvidenceAssemblyRequest,
    EvidenceAssemblyStatus,
    EvidenceProvenanceLink,
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


def _admission(
    status: AdmissionStatus = AdmissionStatus.ADMITTED,
) -> ObservationAdmissionResult:
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
    reasons = (
        (AdmissionReason.OK,)
        if status is AdmissionStatus.ADMITTED
        else (AdmissionReason.UNVERIFIED_PROVENANCE,)
    )
    return ObservationAdmissionResult(
        status=status,
        reason_codes=reasons,
        observation=observation,
        source=source,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        admission_policy_version="admission-1.0.0",
    )


def _link(index: int = 0) -> EvidenceProvenanceLink:
    return EvidenceProvenanceLink(
        link_index=index,
        subject_id="obs-001",
        predicate="derived-from",
        object_id="src-001",
        subject_hash=HASH_B,
        object_hash=HASH_A,
        source_reference="urn:observation:001",
    )


def _request(
    admission: ObservationAdmissionResult | None = None,
    provenance_chain: tuple[EvidenceProvenanceLink, ...] | None = None,
) -> EvidenceAssemblyRequest:
    return EvidenceAssemblyRequest(
        admission_result=_admission() if admission is None else admission,
        provenance_chain=(_link(),) if provenance_chain is None else provenance_chain,
        evidence_id="evidence-001",
        expected_model_version="observation-1.0.0",
        expected_contract_version="L2.1",
        assembly_policy_version="assembly-1.0.0",
    )


def test_admitted_observation_assembles_deterministically() -> None:
    request = _request()
    first = assemble_evidence(request)
    second = assemble_evidence(request)

    assert first == second
    assert first.status is EvidenceAssemblyStatus.ASSEMBLED
    assert first.reason_codes == (EvidenceAssemblyReason.OK,)
    assert first.evidence_record is not None


def test_l20_identities_are_preserved_without_recomputation() -> None:
    request = _request()
    result = assemble_evidence(request)

    assert result.evidence_record is not None
    assert result.evidence_record.observation_hash == request.admission_result.output_hash
    assert result.evidence_record.source_hash == HASH_A


def test_rejected_and_quarantined_sources_cannot_assemble() -> None:
    for status in (AdmissionStatus.REJECTED, AdmissionStatus.QUARANTINED):
        result = assemble_evidence(_request(_admission(status)))

        assert result.status is EvidenceAssemblyStatus.REJECTED
        assert result.evidence_record is None
        assert result.reason_codes[0] is EvidenceAssemblyReason.SOURCE_NOT_ADMITTED


def test_provenance_indices_must_be_exact_and_ordered() -> None:
    result = assemble_evidence(_request(provenance_chain=(_link(1),)))

    assert result.status is EvidenceAssemblyStatus.REJECTED
    assert result.reason_codes == (
        EvidenceAssemblyReason.INVALID_PROVENANCE_CHAIN,
    )


def test_missing_provenance_is_rejected() -> None:
    result = assemble_evidence(_request(provenance_chain=()))

    assert result.status is EvidenceAssemblyStatus.REJECTED
    assert result.reason_codes == (
        EvidenceAssemblyReason.MISSING_PROVENANCE_LINK,
    )


def test_input_objects_remain_unchanged() -> None:
    request = _request()
    before = request.to_payload()

    assemble_evidence(request)

    assert request.to_payload() == before


def test_reason_code_order_is_stable() -> None:
    request = replace(
        _request(_admission(AdmissionStatus.REJECTED), provenance_chain=()),
        expected_model_version="wrong-model",
        expected_contract_version="wrong-contract",
    )
    result = assemble_evidence(request)

    assert result.reason_codes == (
        EvidenceAssemblyReason.SOURCE_NOT_ADMITTED,
        EvidenceAssemblyReason.MISSING_PROVENANCE_LINK,
        EvidenceAssemblyReason.MODEL_VERSION_MISMATCH,
        EvidenceAssemblyReason.CONTRACT_VERSION_MISMATCH,
    )
