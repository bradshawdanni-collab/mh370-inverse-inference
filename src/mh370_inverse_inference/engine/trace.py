"""Immutable per-stage metric records for engine execution traces."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Any

from mh370_inverse_inference.engine.hashing import (
    canonical_json_bytes,
    compose_step_hash,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TraceStatus(StrEnum):
    """Execution status for one trace metric record."""

    OK = "ok"
    FAILED = "failed"
    PARTIAL = "partial"


def _validate_digest(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _validate_optional_non_negative_float(value: float | None, name: str) -> None:
    if value is not None and (not isfinite(value) or value < 0.0):
        raise ValueError(f"{name} must be finite and non-negative")


def _validate_optional_non_negative_int(value: int | None, name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{name} must be non-negative")


def canonical_metadata_json(metadata: Any | None) -> str | None:
    """Return canonical metadata JSON text or ``None`` when absent."""
    if metadata is None:
        return None
    encoded = canonical_json_bytes(metadata)
    parsed = json.loads(encoded.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("metadata must encode a JSON object")
    return encoded.decode("utf-8")


@dataclass(frozen=True, slots=True)
class TraceMetricRecord:
    """Immutable evidence record for one engine execution stage."""

    stage_id: str
    stage_index: int
    input_hash: str
    output_hash: str
    op_signature_hash: str
    trace_hash: str
    duration_ms: float | None = None
    record_count: int | None = None
    hypothesis_count: int | None = None
    normalization_error: float | None = None
    pre_normalization_mass: float | None = None
    status: TraceStatus = TraceStatus.OK
    failure_kind: str | None = None
    metadata_json: str | None = None

    def __post_init__(self) -> None:
        if not self.stage_id:
            raise ValueError("stage_id must be non-empty")
        if self.stage_index < 0:
            raise ValueError("stage_index must be non-negative")
        _validate_digest(self.input_hash, "input_hash")
        _validate_digest(self.output_hash, "output_hash")
        _validate_digest(self.op_signature_hash, "op_signature_hash")
        _validate_digest(self.trace_hash, "trace_hash")
        _validate_optional_non_negative_float(self.duration_ms, "duration_ms")
        _validate_optional_non_negative_int(self.record_count, "record_count")
        _validate_optional_non_negative_int(
            self.hypothesis_count,
            "hypothesis_count",
        )
        _validate_optional_non_negative_float(
            self.normalization_error,
            "normalization_error",
        )
        _validate_optional_non_negative_float(
            self.pre_normalization_mass,
            "pre_normalization_mass",
        )
        if self.status is TraceStatus.FAILED:
            if not self.failure_kind:
                raise ValueError("failure_kind is required when status is failed")
        elif self.failure_kind is not None:
            raise ValueError("failure_kind is only valid when status is failed")
        if self.metadata_json is not None:
            canonical = canonical_metadata_json(json.loads(self.metadata_json))
            if canonical != self.metadata_json:
                raise ValueError("metadata_json must be canonical JSON")

    @classmethod
    def from_parts(
        cls,
        *,
        stage_id: str,
        stage_index: int,
        input_hash: str,
        output_hash: str,
        op_signature_hash: str,
        duration_ms: float | None = None,
        record_count: int | None = None,
        hypothesis_count: int | None = None,
        normalization_error: float | None = None,
        pre_normalization_mass: float | None = None,
        status: TraceStatus = TraceStatus.OK,
        failure_kind: str | None = None,
        metadata: Any | None = None,
    ) -> TraceMetricRecord:
        """Build a record while delegating trace hashing to L10.2."""
        trace_hash = compose_step_hash(
            input_hash=input_hash,
            output_hash=output_hash,
            op_signature_hash=op_signature_hash,
        )
        return cls(
            stage_id=stage_id,
            stage_index=stage_index,
            input_hash=input_hash,
            output_hash=output_hash,
            op_signature_hash=op_signature_hash,
            trace_hash=trace_hash,
            duration_ms=duration_ms,
            record_count=record_count,
            hypothesis_count=hypothesis_count,
            normalization_error=normalization_error,
            pre_normalization_mass=pre_normalization_mass,
            status=status,
            failure_kind=failure_kind,
            metadata_json=canonical_metadata_json(metadata),
        )
