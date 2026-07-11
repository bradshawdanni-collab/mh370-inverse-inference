"""Trace mapping for deterministic L2.1 evidence-assembly results."""

from __future__ import annotations

from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.evidence.models import (
    EvidenceAssemblyResult,
    EvidenceAssemblyStatus,
)


def evidence_trace_record(
    result: EvidenceAssemblyResult,
    *,
    stage_index: int,
    duration_ms: float | None = None,
) -> TraceMetricRecord:
    """Map an evidence-assembly result into the shared L10 trace contract."""
    assembled = result.status is EvidenceAssemblyStatus.ASSEMBLED
    record = result.evidence_record
    observation = result.admission_result.observation

    metadata = {
        "assembly_policy_version": result.assembly_policy_version,
        "assembly_status": result.status.value,
        "contract_version": (record.contract_version if record is not None else None),
        "evidence_id": record.evidence_id if record is not None else None,
        "model_version": record.model_version if record is not None else None,
        "observation_id": observation.observation_id,
        "observation_type": observation.observation_type.value,
        "provenance_link_count": (
            len(record.provenance_chain) if record is not None else 0
        ),
        "reason_codes": [reason.value for reason in result.reason_codes],
        "source_id": observation.source_id,
    }

    return TraceMetricRecord.from_parts(
        stage_id=result.operation,
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        duration_ms=duration_ms,
        record_count=1 if assembled else 0,
        hypothesis_count=None,
        normalization_error=None,
        pre_normalization_mass=None,
        status=TraceStatus.OK if assembled else TraceStatus.FAILED,
        failure_kind=None if assembled else result.reason_codes[0].value,
        metadata=metadata,
    )
