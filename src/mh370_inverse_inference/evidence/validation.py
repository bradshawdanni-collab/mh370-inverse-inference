"""Pure deterministic conformance validation for L2.2 evidence packages."""

from __future__ import annotations

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.models import EvidenceAssemblyStatus
from mh370_inverse_inference.evidence.validation_models import (
    CONTRACT_VERSION,
    OPERATION,
    EvidenceValidationReason,
    EvidenceValidationRequest,
    EvidenceValidationResult,
    EvidenceValidationStatus,
)


def _provenance_reasons(
    request: EvidenceValidationRequest,
) -> list[EvidenceValidationReason]:
    record = request.assembly_result.evidence_record
    if record is None:
        return []

    chain = record.provenance_chain
    expected_indices = tuple(range(len(chain)))
    actual_indices = tuple(link.link_index for link in chain)
    reasons: list[EvidenceValidationReason] = []

    if not chain or actual_indices != expected_indices:
        reasons.append(EvidenceValidationReason.INVALID_PROVENANCE_CHAIN)
        return reasons

    first = chain[0]
    if (
        first.subject_id != record.observation_id
        or first.subject_hash != record.observation_hash
        or first.object_id != record.source_id
        or first.object_hash != record.source_hash
    ):
        reasons.append(EvidenceValidationReason.PROVENANCE_HASH_DISCONTINUITY)

    for previous, current in zip(chain, chain[1:], strict=False):
        if (
            previous.object_id != current.subject_id
            or previous.object_hash != current.subject_hash
        ):
            reasons.append(EvidenceValidationReason.PROVENANCE_HASH_DISCONTINUITY)
            break

    return reasons


def _reason_codes(
    request: EvidenceValidationRequest,
) -> tuple[EvidenceValidationReason, ...]:
    assembly = request.assembly_result
    record = assembly.evidence_record
    reasons: list[EvidenceValidationReason] = []

    if assembly.status is not EvidenceAssemblyStatus.ASSEMBLED:
        reasons.append(EvidenceValidationReason.ASSEMBLY_NOT_COMPLETE)
    if record is None:
        reasons.append(EvidenceValidationReason.MISSING_EVIDENCE_RECORD)
        return tuple(dict.fromkeys(reasons))

    if request.expected_contract_version != CONTRACT_VERSION:
        reasons.append(EvidenceValidationReason.CONTRACT_VERSION_MISMATCH)

    evidence_hash = sha256_payload(record.to_payload())
    if evidence_hash != request.expected_evidence_hash:
        reasons.append(EvidenceValidationReason.EVIDENCE_HASH_MISMATCH)

    admission = assembly.admission_result
    if (
        record.observation_id != admission.observation.observation_id
        or record.observation_type is not admission.observation.observation_type
        or record.observation_hash != admission.output_hash
    ):
        reasons.append(EvidenceValidationReason.OBSERVATION_IDENTITY_MISMATCH)

    source = admission.source
    if (
        source is None
        or record.source_id != admission.observation.source_id
        or record.source_hash != source.content_hash
    ):
        reasons.append(EvidenceValidationReason.SOURCE_IDENTITY_MISMATCH)

    reasons.extend(_provenance_reasons(request))
    return tuple(dict.fromkeys(reasons)) or (EvidenceValidationReason.OK,)


def validate_evidence(
    request: EvidenceValidationRequest,
) -> EvidenceValidationResult:
    """Validate one assembled evidence package without interpreting it."""
    reason_codes = _reason_codes(request)
    valid = reason_codes == (EvidenceValidationReason.OK,)
    status = (
        EvidenceValidationStatus.VALID if valid else EvidenceValidationStatus.REJECTED
    )

    input_hash = sha256_payload(request.to_payload())
    op_signature_hash = sha256_payload(
        {
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
            "validation_policy_version": request.validation_policy_version,
        }
    )
    output_hash = sha256_payload(
        {
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
    )

    return EvidenceValidationResult(
        status=status,
        reason_codes=reason_codes,
        assembly_result=request.assembly_result,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        validation_policy_version=request.validation_policy_version,
    )
