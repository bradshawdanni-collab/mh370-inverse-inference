"""Pure deterministic L3.0 registered-evidence consumption gate."""

from __future__ import annotations

from mh370_inverse_inference.consumption.models import (
    CONTRACT_VERSION,
    OPERATION,
    AcceptedEvidenceProjection,
    ConsumptionReason,
    ConsumptionStatus,
    EvidenceConsumptionRequest,
    EvidenceConsumptionResult,
    projection_is_well_formed,
)
from mh370_inverse_inference.engine.hashing import sha256_payload


def _reason_codes(
    request: EvidenceConsumptionRequest,
) -> tuple[ConsumptionReason, ...]:
    projection = request.evidence
    reasons: list[ConsumptionReason] = []

    if request.expected_contract_version != CONTRACT_VERSION:
        reasons.append(ConsumptionReason.UNSUPPORTED_CONTRACT_VERSION)
    if not projection_is_well_formed(projection):
        reasons.append(ConsumptionReason.MALFORMED_REGISTERED_IDENTITY)
    if not all(
        (
            projection.evidence_id,
            projection.observation_id,
            projection.source_id,
        )
    ):
        reasons.append(ConsumptionReason.MISSING_REQUIRED_IDENTITY)
    if projection.registry_evidence_id != request.expected_registry_evidence_id:
        reasons.append(ConsumptionReason.REGISTRY_ID_MISMATCH)

    return tuple(dict.fromkeys(reasons)) or (ConsumptionReason.OK,)


def consume_registered_evidence(
    request: EvidenceConsumptionRequest,
) -> EvidenceConsumptionResult:
    """Admit one registry-derived projection without interpreting evidence."""
    reason_codes = _reason_codes(request)
    accepted = reason_codes == (ConsumptionReason.OK,)
    status = ConsumptionStatus.ACCEPTED if accepted else ConsumptionStatus.REJECTED

    accepted_projection = (
        AcceptedEvidenceProjection.from_projection(request.evidence)
        if accepted
        else None
    )
    input_hash = sha256_payload(request.to_payload())
    op_signature_hash = sha256_payload(
        {
            "consumption_policy_version": request.consumption_policy_version,
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
        }
    )
    output_hash = sha256_payload(
        {
            "accepted_projection": (
                None
                if accepted_projection is None
                else accepted_projection.to_payload()
            ),
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
    )

    return EvidenceConsumptionResult(
        status=status,
        reason_codes=reason_codes,
        accepted_projection=accepted_projection,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        consumption_policy_version=request.consumption_policy_version,
    )
