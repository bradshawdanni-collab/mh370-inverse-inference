"""Deterministic SHA-256 verification for provenance-governed artifact bytes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mh370_inverse_inference.engine.hashing import sha256_bytes
from mh370_inverse_inference.provenance.models import ArtifactReference, SourceReference

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest(value: str, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class ChecksumVerification:
    """Immutable result of verifying exact bytes against an expected digest."""

    expected_sha256: str
    actual_sha256: str
    matches: bool

    def __post_init__(self) -> None:
        _digest(self.expected_sha256, "expected_sha256")
        _digest(self.actual_sha256, "actual_sha256")
        if type(self.matches) is not bool:
            raise TypeError("matches must be bool")
        if self.matches != (self.expected_sha256 == self.actual_sha256):
            raise ValueError("matches must reflect the digest comparison")

    def to_payload(self) -> dict[str, str | bool]:
        """Return a deterministic machine-readable verification payload."""
        return {
            "actual_sha256": self.actual_sha256,
            "expected_sha256": self.expected_sha256,
            "matches": self.matches,
        }


def compute_sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest of exact immutable bytes."""
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    return sha256_bytes(payload)


def verify_sha256(payload: bytes, expected_sha256: str) -> ChecksumVerification:
    """Verify exact bytes against one explicit lowercase SHA-256 digest."""
    expected = _digest(expected_sha256, "expected_sha256")
    actual = compute_sha256(payload)
    return ChecksumVerification(
        expected_sha256=expected,
        actual_sha256=actual,
        matches=actual == expected,
    )


def verify_artifact_bytes(
    payload: bytes,
    artifact: ArtifactReference,
) -> ChecksumVerification:
    """Verify exact bytes against an artifact reference without normalization."""
    if type(artifact) is not ArtifactReference:
        raise TypeError("artifact must be ArtifactReference")
    return verify_sha256(payload, artifact.sha256)


def verify_source_bytes(
    payload: bytes,
    source: SourceReference,
) -> ChecksumVerification:
    """Verify exact bytes against a source reference without normalization."""
    if type(source) is not SourceReference:
        raise TypeError("source must be SourceReference")
    return verify_sha256(payload, source.content_hash)
