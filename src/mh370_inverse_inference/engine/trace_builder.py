"""Assembler for immutable engine execution traces."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.engine.hashing import compose_replay_hash
from mh370_inverse_inference.engine.trace import TraceMetricRecord


@dataclass(frozen=True, slots=True)
class ExecutionTrace:
    """Immutable ordered collection of trace metric records."""

    records: tuple[TraceMetricRecord, ...]
    trace_hash: str

    def __post_init__(self) -> None:
        if not self.records:
            raise ValueError("records cannot be empty")

    @property
    def stage_count(self) -> int:
        """Return the number of stages represented in the trace."""
        return len(self.records)


class TraceBuilder:
    """Collect trace records and finalize them into an immutable trace."""

    def __init__(self) -> None:
        self._records: list[TraceMetricRecord] = []
        self._stage_ids: set[str] = set()
        self._stage_indices: set[int] = set()
        self._finished: ExecutionTrace | None = None

    def add(self, record: TraceMetricRecord) -> None:
        """Append one trace record after validating sequence invariants."""
        if not isinstance(record, TraceMetricRecord):
            raise TypeError("expected TraceMetricRecord")
        if self._finished is not None:
            raise ValueError("cannot add records after finish")
        if record.stage_id in self._stage_ids:
            raise ValueError(f"duplicate stage_id: {record.stage_id}")
        if record.stage_index in self._stage_indices:
            raise ValueError(f"duplicate stage_index: {record.stage_index}")
        if self._records and record.stage_index <= self._records[-1].stage_index:
            raise ValueError("stage_index must increase monotonically")

        self._records.append(record)
        self._stage_ids.add(record.stage_id)
        self._stage_indices.add(record.stage_index)

    def finish(self) -> ExecutionTrace:
        """Finalize and return immutable execution trace evidence."""
        if self._finished is not None:
            return self._finished
        if not self._records:
            raise ValueError("cannot finish empty trace")

        trace_hash = compose_replay_hash(
            step_hashes=tuple(record.trace_hash for record in self._records),
            final_posterior_hash=self._records[-1].trace_hash,
        )
        self._finished = ExecutionTrace(
            records=tuple(self._records),
            trace_hash=trace_hash,
        )
        return self._finished
