"""Tests for the L10.4 execution trace builder."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.engine.hashing import compose_replay_hash
from mh370_inverse_inference.engine.trace import TraceMetricRecord
from mh370_inverse_inference.engine.trace_builder import ExecutionTrace, TraceBuilder

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64


def make_record(
    stage_id: str,
    stage_index: int,
    trace_hash: str,
) -> TraceMetricRecord:
    return TraceMetricRecord(
        stage_id=stage_id,
        stage_index=stage_index,
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        trace_hash=trace_hash,
    )


def test_builder_rejects_wrong_record_type() -> None:
    builder = TraceBuilder()

    with pytest.raises(TypeError, match="expected TraceMetricRecord"):
        builder.add("not-a-record")  # type: ignore[arg-type]


def test_builder_rejects_empty_trace_on_finish() -> None:
    builder = TraceBuilder()

    with pytest.raises(ValueError, match="empty trace"):
        builder.finish()


def test_builder_returns_immutable_execution_trace() -> None:
    builder = TraceBuilder()
    record = make_record("adapter", 0, HASH_D)
    builder.add(record)

    trace = builder.finish()

    assert trace.records == (record,)
    assert trace.stage_count == 1
    with pytest.raises(FrozenInstanceError):
        trace.trace_hash = HASH_E
    with pytest.raises(TypeError):
        trace.records[0] = record


def test_builder_finish_is_idempotent() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 0, HASH_D))

    first = builder.finish()
    second = builder.finish()

    assert first is second


def test_builder_rejects_add_after_finish() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 0, HASH_D))
    builder.finish()

    with pytest.raises(ValueError, match="after finish"):
        builder.add(make_record("fusion", 1, HASH_E))


def test_builder_rejects_duplicate_stage_id() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 0, HASH_D))

    with pytest.raises(ValueError, match="duplicate stage_id"):
        builder.add(make_record("adapter", 1, HASH_E))


def test_builder_rejects_duplicate_stage_index() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 0, HASH_D))

    with pytest.raises(ValueError, match="duplicate stage_index"):
        builder.add(make_record("fusion", 0, HASH_E))


def test_builder_rejects_nonmonotonic_stage_index() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 2, HASH_D))

    with pytest.raises(ValueError, match="monotonically"):
        builder.add(make_record("fusion", 1, HASH_E))


def test_identical_record_sequences_produce_identical_trace_hashes() -> None:
    first = TraceBuilder()
    second = TraceBuilder()
    for builder in (first, second):
        builder.add(make_record("adapter", 0, HASH_D))
        builder.add(make_record("fusion", 1, HASH_E))

    assert first.finish().trace_hash == second.finish().trace_hash


def test_record_order_changes_trace_hash() -> None:
    first = TraceBuilder()
    first.add(make_record("adapter", 0, HASH_D))
    first.add(make_record("fusion", 1, HASH_E))

    second = TraceBuilder()
    second.add(make_record("fusion", 0, HASH_E))
    second.add(make_record("adapter", 1, HASH_D))

    assert first.finish().trace_hash != second.finish().trace_hash


def test_record_hash_change_changes_trace_hash() -> None:
    first = TraceBuilder()
    first.add(make_record("adapter", 0, HASH_D))
    first.add(make_record("fusion", 1, HASH_E))

    second = TraceBuilder()
    second.add(make_record("adapter", 0, HASH_D))
    second.add(make_record("fusion", 1, HASH_F))

    assert first.finish().trace_hash != second.finish().trace_hash


def test_trace_hash_delegates_to_ordered_hash_composition() -> None:
    builder = TraceBuilder()
    builder.add(make_record("adapter", 0, HASH_D))
    builder.add(make_record("fusion", 1, HASH_E))

    trace = builder.finish()

    assert trace.trace_hash == compose_replay_hash(
        step_hashes=(HASH_D, HASH_E),
        final_posterior_hash=HASH_E,
    )


def test_execution_trace_rejects_empty_records_directly() -> None:
    with pytest.raises(ValueError, match="records cannot be empty"):
        ExecutionTrace(records=(), trace_hash=HASH_D)
