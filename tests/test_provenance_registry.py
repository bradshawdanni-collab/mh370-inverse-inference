"""Tests for Issue #9B deterministic checksum and local registry behavior."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import (
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    ProvenanceRegistrySnapshot,
    SourceReference,
    build_registry_snapshot,
    compute_sha256,
    contains_reference,
    list_artifact_versions,
    list_by_admission_state,
    lookup_record,
    register_record,
    verify_artifact_bytes,
    verify_sha256,
    verify_source_bytes,
)


def _source_record(
    artifact_id: str,
    version: str,
    payload: bytes,
    *,
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> ArtifactProvenanceRecord:
    digest = compute_sha256(payload)
    artifact = ArtifactReference(
        artifact_id=artifact_id,
        version=version,
        sha256=digest,
    )
    source = SourceReference(
        source_id=f"source:{artifact_id}:{version}",
        publisher="test-publisher",
        title=f"Test source {artifact_id} {version}",
        reference_uri=f"repository://tests/{artifact_id}/{version}",
        retrieved_at_utc="2026-07-28T00:00:00Z",
        licence_or_terms="test-only",
        content_hash=digest,
    )
    return ArtifactProvenanceRecord(
        artifact=artifact,
        kind=ArtifactKind.SOURCE,
        admission_state=admission_state,
        source=source,
        transformation_history=(),
        uncertainty_notes=(),
        limitations=(),
    )


def test_checksum_verification_is_exact_and_deterministic() -> None:
    payload = b"canonical provenance bytes\n"
    digest = compute_sha256(payload)

    first = verify_sha256(payload, digest)
    second = verify_sha256(payload, digest)

    assert first == second
    assert first.matches is True
    assert first.actual_sha256 == digest
    assert first.expected_sha256 == digest
    assert first.to_payload() == second.to_payload()

    mismatch = verify_sha256(payload + b"changed", digest)
    assert mismatch.matches is False
    assert mismatch.actual_sha256 != mismatch.expected_sha256


def test_checksum_verification_rejects_ambiguous_inputs() -> None:
    with pytest.raises(TypeError, match="payload must be bytes"):
        compute_sha256(bytearray(b"mutable"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="lowercase SHA-256"):
        verify_sha256(b"payload", "ABC")


def test_artifact_and_source_verification_use_declared_exact_hashes() -> None:
    payload = b"source bytes"
    record = _source_record("artifact-a", "v1", payload)

    artifact_result = verify_artifact_bytes(payload, record.artifact)
    source_result = verify_source_bytes(payload, record.source)

    assert artifact_result.matches is True
    assert source_result.matches is True
    assert artifact_result.actual_sha256 == record.artifact.sha256
    assert source_result.actual_sha256 == record.source.content_hash


def test_registry_snapshot_canonicalizes_order_and_hashes_identically() -> None:
    first = _source_record("artifact-b", "v1", b"b")
    second = _source_record("artifact-a", "v1", b"a")

    forward = build_registry_snapshot((first, second))
    reverse = build_registry_snapshot((second, first))

    assert forward == reverse
    assert forward.snapshot_sha256 == reverse.snapshot_sha256
    assert tuple(record.artifact.artifact_id for record in forward.records) == (
        "artifact-a",
        "artifact-b",
    )
    assert forward.to_payload() == reverse.to_payload()


def test_registry_snapshot_is_immutable_and_detects_hash_tampering() -> None:
    snapshot = build_registry_snapshot((_source_record("artifact-a", "v1", b"a"),))

    with pytest.raises(FrozenInstanceError):
        snapshot.snapshot_sha256 = "0" * 64  # type: ignore[misc]

    with pytest.raises(ValueError, match="does not match canonical records"):
        ProvenanceRegistrySnapshot(
            records=snapshot.records,
            snapshot_sha256="0" * 64,
        )


def test_registry_rejects_conflicting_artifact_id_and_version() -> None:
    first = _source_record("artifact-a", "v1", b"first")
    conflicting = _source_record("artifact-a", "v1", b"second")

    with pytest.raises(ValueError, match="identify exactly one registry record"):
        build_registry_snapshot((first, conflicting))


def test_register_record_returns_new_snapshot_without_mutating_old_one() -> None:
    v1 = _source_record("artifact-a", "v1", b"one")
    v2 = _source_record(
        "artifact-a",
        "v2",
        b"two",
        admission_state=ArtifactAdmissionState.VERIFIED,
    )
    original = build_registry_snapshot((v1,))

    updated = register_record(original, v2)

    assert len(original.records) == 1
    assert len(updated.records) == 2
    assert updated.snapshot_sha256 != original.snapshot_sha256
    assert list_artifact_versions(updated, "artifact-a") == (v1, v2)
    assert lookup_record(updated, "artifact-a", "v2") == v2
    assert contains_reference(updated, v2.artifact) is True
    assert list_by_admission_state(updated, ArtifactAdmissionState.VERIFIED) == (v2,)

    with pytest.raises(ValueError, match="already registered"):
        register_record(updated, v2)


def test_registry_lookup_requires_exact_version_and_never_falls_back() -> None:
    v1 = _source_record("artifact-a", "v1", b"one")
    snapshot = build_registry_snapshot((v1,))

    assert lookup_record(snapshot, "artifact-a", "v1") == v1
    assert lookup_record(snapshot, "artifact-a", "v2") is None
    assert contains_reference(snapshot, v1.artifact) is True
    assert contains_reference(
        snapshot,
        ArtifactReference(
            artifact_id="artifact-a",
            version="v1",
            sha256="0" * 64,
        ),
    ) is False
