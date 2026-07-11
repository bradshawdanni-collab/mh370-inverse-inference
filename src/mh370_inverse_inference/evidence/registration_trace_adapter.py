"""Trace mapping for deterministic L2.3 evidence registration."""

from __future__ import annotations

from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.evidence.registration_models import (
    EvidenceRegistrationResult,
    EvidenceRegistrationStatus,
)


def registration_result_to_trace(
    result: EvidenceRegistrationResult,
    *,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one registration result into the shared immutable trace contract."""
    registered = result.status is EvidenceRegistrationStatus.REGISTERED
    return TraceMetricRecord.from_parts(
        stage_id="L2.3-evidence-registration",
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        record_count=1 if registered else 0,
        status=TraceStatus.OK if registered else TraceStatus.FAILED,
        failure_kind=None if registered else result.reason_codes[0].value,
        metadata={
            "operation": result.operation,
            "reason_codes": [reason.value for reason in result.reason_codes],
            "registry_policy_version": result.registry_policy_version,
        },
    )
