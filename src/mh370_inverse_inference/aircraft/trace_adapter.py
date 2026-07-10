"""Structural adapter from L1.3 reachability summaries to L10 traces."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.aircraft.envelope import ReachabilitySummary
from mh370_inverse_inference.engine.trace import TraceMetricRecord


@dataclass(frozen=True, slots=True)
class ReachabilityTraceAdapter:
    """Map reachability evidence into the common immutable trace contract."""

    @staticmethod
    def adapt(
        summary: ReachabilitySummary,
        *,
        stage_index: int,
        duration_ms: float | None = None,
    ) -> TraceMetricRecord:
        """Translate a summary without recomputing model or identity hashes."""
        metadata = {
            "contract_version": summary.request.contract_version,
            "control_count": summary.envelope_metadata.control_count,
            "constraint_violation_count": (
                summary.envelope_metadata.constraint_violation_count
            ),
            "dt_seconds": summary.request.dt_seconds,
            "envelope_metadata": summary.envelope_metadata.to_payload(),
            "model_version": summary.request.model_version,
            "state_count": summary.envelope_metadata.state_count,
            "step_count": summary.request.step_count,
        }
        return TraceMetricRecord.from_parts(
            stage_id=summary.operation,
            stage_index=stage_index,
            input_hash=summary.input_hash,
            output_hash=summary.output_hash,
            op_signature_hash=summary.op_signature_hash,
            duration_ms=duration_ms,
            record_count=summary.reachable_state_count,
            metadata=metadata,
        )
