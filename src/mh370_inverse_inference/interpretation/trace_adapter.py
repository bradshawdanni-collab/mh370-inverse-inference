"""Shared trace mapping for deterministic L3 interpretation execution."""

from __future__ import annotations

from mh370_inverse_inference.engine.hashing import compose_step_hash
from mh370_inverse_inference.engine.trace import TraceMetricRecord, TraceStatus
from mh370_inverse_inference.interpretation.executor import NeutralRuleExecution
from mh370_inverse_inference.interpretation.result import (
    InterpretationReason,
    InterpretationResult,
    InterpretationStatus,
)

STAGE_ID = "L3.6-neutral-interpretation-execution"


def _trace_status(status: InterpretationStatus) -> TraceStatus:
    if status is InterpretationStatus.ACCEPTED:
        return TraceStatus.OK
    if status is InterpretationStatus.INSUFFICIENT_EVIDENCE:
        return TraceStatus.PARTIAL
    return TraceStatus.FAILED


def interpretation_result_to_trace(
    result: InterpretationResult,
    *,
    op_signature_hash: str,
    rule_id: str,
    rule_version: str,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one L3 interpretation result into the shared trace contract."""
    if type(result) is not InterpretationResult:
        raise TypeError("result must be InterpretationResult")
    if not rule_id.strip():
        raise ValueError("rule_id cannot be blank")
    if not rule_version.strip():
        raise ValueError("rule_version cannot be blank")

    status = _trace_status(result.status)
    failure_kind = None
    if status is TraceStatus.FAILED:
        failure_kind = result.reason_codes[0].value

    return TraceMetricRecord.from_parts(
        stage_id=STAGE_ID,
        stage_index=stage_index,
        input_hash=result.input_hash,
        output_hash=result.result_hash,
        op_signature_hash=op_signature_hash,
        record_count=len(result.derived_claims),
        status=status,
        failure_kind=failure_kind,
        metadata={
            "claim_hashes": [claim.claim_hash for claim in result.derived_claims],
            "interpretation_contract_version": result.interpretation_contract_version,
            "interpretation_policy_version": result.interpretation_policy_version,
            "reason_codes": [reason.value for reason in result.reason_codes],
            "rule_id": rule_id,
            "rule_version": rule_version,
        },
    )


def neutral_rule_execution_to_trace(
    execution: NeutralRuleExecution,
    *,
    stage_index: int,
) -> TraceMetricRecord:
    """Map one deterministic neutral-rule execution into shared trace form."""
    if type(execution) is not NeutralRuleExecution:
        raise TypeError("execution must be NeutralRuleExecution")
    return interpretation_result_to_trace(
        execution.result,
        op_signature_hash=execution.op_signature_hash,
        rule_id=execution.rule_id.value,
        rule_version=execution.rule_version,
        stage_index=stage_index,
    )


def build_nonaccepted_interpretation_trace(
    result: InterpretationResult,
    *,
    op_signature_hash: str,
    rule_id: str,
    rule_version: str,
    stage_index: int,
) -> TraceMetricRecord:
    """Trace a withheld or insufficient-support L3 result without execution."""
    if result.status is InterpretationStatus.ACCEPTED:
        raise ValueError("result must be non-accepted")
    if result.reason_codes == (InterpretationReason.OK,):
        raise ValueError("non-accepted result cannot use OK reason")
    return interpretation_result_to_trace(
        result,
        op_signature_hash=op_signature_hash,
        rule_id=rule_id,
        rule_version=rule_version,
        stage_index=stage_index,
    )


def verify_interpretation_trace(trace: TraceMetricRecord) -> bool:
    """Return whether an L3.6 trace retains its deterministic step identity."""
    if type(trace) is not TraceMetricRecord:
        raise TypeError("trace must be TraceMetricRecord")
    if trace.stage_id != STAGE_ID:
        return False
    expected = compose_step_hash(
        input_hash=trace.input_hash,
        output_hash=trace.output_hash,
        op_signature_hash=trace.op_signature_hash,
    )
    return trace.trace_hash == expected
