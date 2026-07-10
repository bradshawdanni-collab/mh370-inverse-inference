"""Canonical serialization helpers for aircraft dynamics records."""

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
