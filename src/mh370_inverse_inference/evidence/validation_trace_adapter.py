"""Trace mapping for deterministic L2.2 evidence validation."""

from __future__ import annotations

from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.evidence.validation_models import (
    EvidenceValidationResult,
    EvidenceValidationStatus,
)


def validation_result_to_trace(
    result: EvidenceValidationResult,
    *,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one validation result into the shared immutable trace contract."""
    valid = result.status is EvidenceValidationStatus.VALID
    return TraceMetricRecord.from_parts(
        stage_id="L2.2-evidence-validation",
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        record_count=1,
        status=TraceStatus.OK if valid else TraceStatus.FAILED,
        failure_kind=None if valid else result.reason_codes[0].value,
        metadata={
            "operation": result.operation,
            "reason_codes": [reason.value for reason in result.reason_codes],
            "validation_policy_version": result.validation_policy_version,
        },
    )
