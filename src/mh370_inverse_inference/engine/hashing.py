"""Canonical JSON and SHA-256 helpers for engine trace verification."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _validate_canonical_value(value: Any, path: str = "$") -> None:
    """Reject values that cannot participate in deterministic JSON hashing."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"non-finite float at {path}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"canonical JSON object keys must be strings at {path}")
            _validate_canonical_value(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_canonical_value(item, f"{path}[{index}]")
        return
    raise TypeError(f"unsupported canonical JSON value at {path}: {type(value).__name__}")


def canonical_json_bytes(payload: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for a supported payload."""
    _validate_canonical_value(payload)
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 digest for raw bytes."""
    return hashlib.sha256(payload).hexdigest()


def sha256_payload(payload: Any) -> str:
    """Return a SHA-256 digest for a canonical JSON payload."""
    return sha256_bytes(canonical_json_bytes(payload))


def _validate_digest(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def compose_step_hash(
    *,
    input_hash: str,
    output_hash: str,
    op_signature_hash: str,
) -> str:
    """Compose a deterministic hash for one ordered engine step."""
    _validate_digest(input_hash, "input_hash")
    _validate_digest(output_hash, "output_hash")
    _validate_digest(op_signature_hash, "op_signature_hash")
    material = f"{input_hash}{output_hash}{op_signature_hash}".encode("ascii")
    return sha256_bytes(material)


def compose_replay_hash(
    *,
    step_hashes: Sequence[str],
    final_posterior_hash: str,
) -> str:
    """Compose a replay hash from ordered step hashes and final posterior hash."""
    if not step_hashes:
        raise ValueError("step_hashes cannot be empty")
    for index, step_hash in enumerate(step_hashes):
        _validate_digest(step_hash, f"step_hashes[{index}]")
    _validate_digest(final_posterior_hash, "final_posterior_hash")
    material = "".join((*step_hashes, final_posterior_hash)).encode("ascii")
    return sha256_bytes(material)
