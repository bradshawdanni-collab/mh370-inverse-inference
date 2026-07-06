"""Tests for immutable engine trace metric records."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.engine.hashing import compose_step_hash
from mh370_inverse_inference.engine.trace import (
    TraceMetricRecord,
    TraceStatus,
    canonical_metadata_json,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def test_trace_metric_record_is_immutable() -> None:
    record = TraceMetricRecord(
        stage_id="stage-1",
        stage_index=0,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        trace_hash=HASH_D,
    )

    with pytest.raises(FrozenInstanceError):
        record.stage_id = "stage-2"


def test_from_parts_delegates_hashing_and_canonicalizes_metadata() -> None:
    record = TraceMetricRecord.from_parts(
        stage_id="fusion",
        stage_index=2,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        duration_ms=12.5,
        record_count=4,
        hypothesis_count=2,
        normalization_error=0.0,
        pre_normalization_mass=0.75,
        metadata={"z": 2, "a": 1},
    )

    assert record.trace_hash == compose_step_hash(
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
    )
    assert record.metadata_json == '{"a":1,"z":2}'
    assert record.status is TraceStatus.OK


def test_canonical_metadata_is_order_independent() -> None:
    first = canonical_metadata_json({"beta": 2, "alpha": 1})
    second = canonical_metadata_json({"alpha": 1, "beta": 2})

    assert first == second == '{"alpha":1,"beta":2}'


def test_metadata_must_encode_an_object() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        canonical_metadata_json([1, 2, 3])


def test_trace_metric_record_rejects_invalid_required_values() -> None:
    with pytest.raises(ValueError, match="stage_id"):
        TraceMetricRecord(
            stage_id="",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            trace_hash=HASH_D,
        )

    with pytest.raises(ValueError, match="stage_index"):
        TraceMetricRecord(
            stage_id="stage-1",
            stage_index=-1,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            trace_hash=HASH_D,
        )


def test_trace_metric_record_rejects_malformed_hashes() -> None:
    with pytest.raises(ValueError, match="input_hash"):
        TraceMetricRecord(
            stage_id="stage-1",
            stage_index=0,
            input_hash="bad",
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            trace_hash=HASH_D,
        )


def test_trace_metric_record_rejects_negative_or_non_finite_metrics() -> None:
    with pytest.raises(ValueError, match="duration_ms"):
        TraceMetricRecord.from_parts(
            stage_id="stage-1",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            duration_ms=-1.0,
        )

    with pytest.raises(ValueError, match="normalization_error"):
        TraceMetricRecord.from_parts(
            stage_id="stage-1",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            normalization_error=float("nan"),
        )


def test_failed_status_requires_failure_kind() -> None:
    with pytest.raises(ValueError, match="required"):
        TraceMetricRecord.from_parts(
            stage_id="stage-1",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            status=TraceStatus.FAILED,
        )


def test_non_failed_status_rejects_failure_kind() -> None:
    with pytest.raises(ValueError, match="only valid"):
        TraceMetricRecord.from_parts(
            stage_id="stage-1",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            status=TraceStatus.PARTIAL,
            failure_kind="timeout",
        )


def test_noncanonical_metadata_json_is_rejected() -> None:
    with pytest.raises(ValueError, match="canonical JSON"):
        TraceMetricRecord(
            stage_id="stage-1",
            stage_index=0,
            input_hash=HASH_A,
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            trace_hash=HASH_D,
            metadata_json='{"z":2, "a":1}',
        )


def test_trace_metric_record_structural_equality() -> None:
    first = TraceMetricRecord.from_parts(
        stage_id="stage-1",
        stage_index=1,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
    )
    second = TraceMetricRecord.from_parts(
        stage_id="stage-1",
        stage_index=1,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
    )

    assert first == second
