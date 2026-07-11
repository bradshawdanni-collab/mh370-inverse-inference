"""Pure deterministic registration for validated L2.3 evidence."""

from __future__ import annotations

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.registration_models import (
    CONTRACT_VERSION,
    OPERATION,
    EvidenceRegistrationReason,
    EvidenceRegistrationRequest,
    EvidenceRegistrationResult,
    EvidenceRegistrationStatus,
    RegisteredEvidenceRecord,
)
from mh370_inverse_inference.evidence.validation_models import (
    CONTRACT_VERSION as VALIDATION_CONTRACT_VERSION,
)
from mh370_inverse_inference.evidence.validation_models import (
    OPERATION as VALIDATION_OPERATION,
)
from mh370_inverse_inference.evidence.validation_models import (
    EvidenceValidationReason,
    EvidenceValidationStatus,
)


def _validation_result_is_consistent(
    request: EvidenceRegistrationRequest,
) -> bool:
    result = request.validation_result
    expected_output_hash = sha256_payload(
        {
            "reason_codes": [reason.value for reason in result.reason_codes],
            "status": result.status.value,
        }
    )
    expected_operation_hash = sha256_payload(
        {
            "contract_version": VALIDATION_CONTRACT_VERSION,
            "operation": VALIDATION_OPERATION,
            "validation_policy_version": result.validation_policy_version,
        }
    )
    valid_shape = (
        result.status is EvidenceValidationStatus.VALID
        and result.reason_codes == (EvidenceValidationReason.OK,)
    )
    return (
        valid_shape
        and result.output_hash == expected_output_hash
        and result.op_signature_hash == expected_operation_hash
    )


def _reason_codes(
    request: EvidenceRegistrationRequest,
) -> tuple[EvidenceRegistrationReason, ...]:
    validation = request.validation_result
    assembly = validation.assembly_result
    record = assembly.evidence_record
    reasons: list[EvidenceRegistrationReason] = []

    if validation.status is not EvidenceValidationStatus.VALID:
        reasons.append(EvidenceRegistrationReason.VALIDATION_NOT_VALID)
    if record is None:
        reasons.append(EvidenceRegistrationReason.MISSING_EVIDENCE_RECORD)
    if request.expected_contract_version != CONTRACT_VERSION:
        reasons.append(EvidenceRegistrationReason.CONTRACT_VERSION_MISMATCH)

    if record is not None:
        evidence_hash = sha256_payload(record.to_payload())
        if evidence_hash != request.expected_evidence_hash:
            reasons.append(EvidenceRegistrationReason.EVIDENCE_HASH_MISMATCH)

    validation_hash = sha256_payload(validation.to_payload())
    if validation_hash != request.expected_validation_hash:
        reasons.append(EvidenceRegistrationReason.VALIDATION_HASH_MISMATCH)

    if not _validation_result_is_consistent(request):
        reasons.append(EvidenceRegistrationReason.VALIDATION_RESULT_INCONSISTENT)

    return tuple(dict.fromkeys(reasons)) or (EvidenceRegistrationReason.OK,)


def register_evidence(
    request: EvidenceRegistrationRequest,
) -> EvidenceRegistrationResult:
    """Register one valid evidence package without re-running prior layers."""
    reason_codes = _reason_codes(request)
    registered = reason_codes == (EvidenceRegistrationReason.OK,)
    status = (
        EvidenceRegistrationStatus.REGISTERED
        if registered
        else EvidenceRegistrationStatus.REJECTED
    )

    input_hash = sha256_payload(request.to_payload())
    op_signature_hash = sha256_payload(
        {
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
            "registry_policy_version": request.registry_policy_version,
        }
    )

    registered_record: RegisteredEvidenceRecord | None = None
    if registered:
        validation = request.validation_result
        evidence_record = validation.assembly_result.evidence_record
        assert evidence_record is not None
        identity_payload = {
            "evidence_record": evidence_record.to_payload(),
            "registration_contract_version": CONTRACT_VERSION,
            "validation_operation_hash": validation.op_signature_hash,
            "validation_output_hash": validation.output_hash,
        }
        registry_evidence_id = sha256_payload(identity_payload)
        registered_record = RegisteredEvidenceRecord(
            registry_evidence_id=registry_evidence_id,
            evidence_id=evidence_record.evidence_id,
            observation_id=evidence_record.observation_id,
            source_id=evidence_record.source_id,
            evidence_hash=request.expected_evidence_hash,
            validation_hash=request.expected_validation_hash,
            validation_output_hash=validation.output_hash,
            validation_operation_hash=validation.op_signature_hash,
        )

    output_hash = sha256_payload(
        {
            "reason_codes": [reason.value for reason in reason_codes],
            "registered_record": (
                None if registered_record is None else registered_record.to_payload()
            ),
            "status": status.value,
        }
    )

    return EvidenceRegistrationResult(
        status=status,
        reason_codes=reason_codes,
        registered_record=registered_record,
        validation_result=request.validation_result,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        registry_policy_version=request.registry_policy_version,
    )
