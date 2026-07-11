"""Pure deterministic evidence assembly for L2.1."""

from __future__ import annotations

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.models import (
    CONTRACT_VERSION,
    OPERATION,
    EvidenceAssemblyReason,
    EvidenceAssemblyRequest,
    EvidenceAssemblyResult,
    EvidenceAssemblyStatus,
    EvidenceRecord,
)
from mh370_inverse_inference.observations.models import AdmissionStatus


def _reason_codes(
    request: EvidenceAssemblyRequest,
) -> tuple[EvidenceAssemblyReason, ...]:
    admission = request.admission_result
    reasons: list[EvidenceAssemblyReason] = []

    if admission.status is not AdmissionStatus.ADMITTED:
        reasons.append(EvidenceAssemblyReason.SOURCE_NOT_ADMITTED)

    if admission.source is None:
        reasons.append(EvidenceAssemblyReason.INVALID_SOURCE_HASH)

    expected_indices = tuple(range(len(request.provenance_chain)))
    actual_indices = tuple(link.link_index for link in request.provenance_chain)
    if not request.provenance_chain:
        reasons.append(EvidenceAssemblyReason.MISSING_PROVENANCE_LINK)
    elif actual_indices != expected_indices:
        reasons.append(EvidenceAssemblyReason.INVALID_PROVENANCE_CHAIN)

    if admission.observation.model_version != request.expected_model_version:
        reasons.append(EvidenceAssemblyReason.MODEL_VERSION_MISMATCH)
    if request.expected_contract_version != CONTRACT_VERSION:
        reasons.append(EvidenceAssemblyReason.CONTRACT_VERSION_MISMATCH)

    return tuple(dict.fromkeys(reasons)) or (EvidenceAssemblyReason.OK,)


def assemble_evidence(request: EvidenceAssemblyRequest) -> EvidenceAssemblyResult:
    """Package admitted observation evidence without interpreting it."""
    reason_codes = _reason_codes(request)
    assembled = reason_codes == (EvidenceAssemblyReason.OK,)
    status = (
        EvidenceAssemblyStatus.ASSEMBLED
        if assembled
        else EvidenceAssemblyStatus.REJECTED
    )

    input_hash = sha256_payload(request.to_payload())
    op_signature_hash = sha256_payload(
        {
            "assembly_policy_version": request.assembly_policy_version,
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
        }
    )

    evidence_record: EvidenceRecord | None = None
    if assembled:
        admission = request.admission_result
        source = admission.source
        assert source is not None
        evidence_record = EvidenceRecord(
            evidence_id=request.evidence_id,
            observation_id=admission.observation.observation_id,
            observation_type=admission.observation.observation_type,
            observation_hash=admission.output_hash,
            source_id=admission.observation.source_id,
            source_hash=source.content_hash,
            provenance_chain=request.provenance_chain,
            assembled_at_policy_version=request.assembly_policy_version,
            model_version=admission.observation.model_version,
        )

    output_hash = sha256_payload(
        {
            "evidence_record": (
                None if evidence_record is None else evidence_record.to_payload()
            ),
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
    )

    return EvidenceAssemblyResult(
        status=status,
        reason_codes=reason_codes,
        evidence_record=evidence_record,
        admission_result=request.admission_result,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        assembly_policy_version=request.assembly_policy_version,
    )
