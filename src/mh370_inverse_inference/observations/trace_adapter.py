"""Trace mapping for deterministic observation-admission results."""

from __future__ import annotations

from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.observations.models import (
    AdmissionStatus,
    ObservationAdmissionResult,
)


def admission_trace_record(
    result: ObservationAdmissionResult,
    *,
    stage_index: int,
    duration_ms: float | None = None,
) -> TraceMetricRecord:
    """Map an admission result into the shared L10 trace contract."""
    failed = result.status is AdmissionStatus.REJECTED
    metadata = {
        "admission_policy_version": result.admission_policy_version,
        "admission_status": result.status.value,
        "contract_version": result.observation.contract_version,
        "model_version": result.observation.model_version,
        "observation_id": result.observation.observation_id,
        "observation_type": result.observation.observation_type.value,
        "reason_codes": [reason.value for reason in result.reason_codes],
        "source_id": result.observation.source_id,
        "units": result.observation.units,
    }
    return TraceMetricRecord.from_parts(
        stage_id=result.operation,
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        duration_ms=duration_ms,
        record_count=1,
        status=TraceStatus.FAILED if failed else TraceStatus.OK,
        failure_kind=result.reason_codes[0].value if failed else None,
        metadata=metadata,
    )
