"""Trace mapping for deterministic L3.0 evidence consumption."""

from __future__ import annotations

from mh370_inverse_inference.consumption.models import (
    ConsumptionStatus,
    EvidenceConsumptionResult,
)
from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus


def consumption_result_to_trace(
    result: EvidenceConsumptionResult,
    *,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one consumption result into the shared immutable trace contract."""
    accepted = result.status is ConsumptionStatus.ACCEPTED
    return TraceMetricRecord.from_parts(
        stage_id="L3.0-registered-evidence-consumption",
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        record_count=1 if accepted else 0,
        status=TraceStatus.OK if accepted else TraceStatus.FAILED,
        failure_kind=None if accepted else result.reason_codes[0].value,
        metadata={
            "consumption_policy_version": result.consumption_policy_version,
            "operation": result.operation,
            "reason_codes": [reason.value for reason in result.reason_codes],
        },
    )
