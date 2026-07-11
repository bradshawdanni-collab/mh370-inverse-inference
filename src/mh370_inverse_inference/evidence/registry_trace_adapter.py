"""Trace mapping for deterministic L2.4 registry queries."""

from __future__ import annotations

from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.evidence.registry_models import (
    EvidenceRegistryResult,
    EvidenceRegistryStatus,
)


def registry_result_to_trace(
    result: EvidenceRegistryResult,
    *,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one registry result into the shared immutable trace contract."""
    found = result.status is EvidenceRegistryStatus.FOUND
    return TraceMetricRecord.from_parts(
        stage_id="L2.4-evidence-registry",
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.output_hash,
        op_signature_hash=result.op_signature_hash,
        record_count=1 if found else 0,
        status=TraceStatus.OK if found else TraceStatus.FAILED,
        failure_kind=None if found else result.reason_codes[0].value,
        metadata={
            "operation": result.operation,
            "reason_codes": [reason.value for reason in result.reason_codes],
            "registry_policy_version": result.registry_policy_version,
            "snapshot_hash": result.snapshot_hash,
        },
    )
