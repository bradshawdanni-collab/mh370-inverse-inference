"""Canonical serialization and identity helpers for aircraft dynamics."""

from __future__ import annotations

from typing import Any, Protocol

from mh370_inverse_inference.engine.hashing import canonical_json_bytes, sha256_payload


class CanonicalRecord(Protocol):
    """Protocol for aircraft records that expose canonical payloads."""

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible payload."""


def canonical_json(record: CanonicalRecord) -> str:
    """Serialize a record to deterministic canonical JSON text."""
    return canonical_json_bytes(record.to_payload()).decode("utf-8")


def canonical_hash(record: CanonicalRecord) -> str:
    """Return the SHA-256 hash of a record's canonical JSON payload."""
    return sha256_payload(record.to_payload())


def dynamics_input_hash(
    *,
    previous_state: dict[str, Any],
    control_input: dict[str, Any],
    dt_seconds: float,
    model_version: str,
) -> str:
    """Hash the exact canonical identity of a dynamics request."""
    return sha256_payload(
        {
            "control_input": control_input,
            "dt_seconds": dt_seconds,
            "model_version": model_version,
            "previous_state": previous_state,
        }
    )


def dynamics_output_hash(
    *,
    next_state: dict[str, Any],
    metrics: dict[str, Any],
) -> str:
    """Hash the exact canonical identity of a dynamics output."""
    return sha256_payload({"metrics": metrics, "next_state": next_state})


def dynamics_operation_hash(
    *,
    operation: str,
    contract_version: str,
    model_version: str,
) -> str:
    """Hash the deterministic operation signature."""
    return sha256_payload(
        {
            "contract_version": contract_version,
            "model_version": model_version,
            "operation": operation,
        }
    )
