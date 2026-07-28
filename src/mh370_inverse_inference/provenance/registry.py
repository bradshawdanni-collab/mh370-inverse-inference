"""Immutable deterministic local registry for repository provenance records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.provenance.models import (
    ArtifactAdmissionState,
    ArtifactProvenanceRecord,
    ArtifactReference,
)

REGISTRY_CONTRACT_VERSION = "PROVENANCE-REGISTRY-1"


def _non_empty(value: str, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")
    return value


def _record_key(record: ArtifactProvenanceRecord) -> tuple[str, str, str]:
    return (
        record.artifact.artifact_id,
        record.artifact.version,
        record.artifact.sha256,
    )


def registry_identity_payload(
    records: tuple[ArtifactProvenanceRecord, ...],
) -> dict[str, Any]:
    """Return the canonical identity payload for one local registry snapshot."""
    return {
        "contract_version": REGISTRY_CONTRACT_VERSION,
        "records": [record.to_payload() for record in records],
    }


@dataclass(frozen=True, slots=True)
class ProvenanceRegistrySnapshot:
    """Immutable canonically ordered snapshot of exact artifact provenance."""

    records: tuple[ArtifactProvenanceRecord, ...]
    snapshot_sha256: str
    contract_version: str = REGISTRY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.records) is not tuple:
            raise TypeError("records must be tuple")
        if any(type(record) is not ArtifactProvenanceRecord for record in self.records):
            raise TypeError("records must contain ArtifactProvenanceRecord values")
        if self.contract_version != REGISTRY_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{REGISTRY_CONTRACT_VERSION}"
            )

        keys = tuple(_record_key(record) for record in self.records)
        if keys != tuple(sorted(keys)):
            raise ValueError("records must use canonical artifact ordering")

        version_keys = tuple(
            (record.artifact.artifact_id, record.artifact.version)
            for record in self.records
        )
        if len(version_keys) != len(set(version_keys)):
            raise ValueError(
                "artifact_id and version must identify exactly one registry record"
            )

        expected = sha256_payload(registry_identity_payload(self.records))
        if self.snapshot_sha256 != expected:
            raise ValueError("snapshot_sha256 does not match canonical records")

    def to_payload(self) -> dict[str, Any]:
        """Return the deterministic registry snapshot payload."""
        return {
            "contract_version": self.contract_version,
            "records": [record.to_payload() for record in self.records],
            "snapshot_sha256": self.snapshot_sha256,
        }


def build_registry_snapshot(
    records: tuple[ArtifactProvenanceRecord, ...],
) -> ProvenanceRegistrySnapshot:
    """Build a canonical immutable registry snapshot from local records."""
    if type(records) is not tuple:
        raise TypeError("records must be tuple")
    if any(type(record) is not ArtifactProvenanceRecord for record in records):
        raise TypeError("records must contain ArtifactProvenanceRecord values")

    ordered = tuple(sorted(records, key=_record_key))
    snapshot_sha256 = sha256_payload(registry_identity_payload(ordered))
    return ProvenanceRegistrySnapshot(
        records=ordered,
        snapshot_sha256=snapshot_sha256,
    )


def register_record(
    snapshot: ProvenanceRegistrySnapshot,
    record: ArtifactProvenanceRecord,
) -> ProvenanceRegistrySnapshot:
    """Return a new snapshot with one previously unregistered artifact version."""
    if type(snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("snapshot must be ProvenanceRegistrySnapshot")
    if type(record) is not ArtifactProvenanceRecord:
        raise TypeError("record must be ArtifactProvenanceRecord")

    identity = (record.artifact.artifact_id, record.artifact.version)
    if any(
        (existing.artifact.artifact_id, existing.artifact.version) == identity
        for existing in snapshot.records
    ):
        raise ValueError("artifact_id and version are already registered")

    return build_registry_snapshot((*snapshot.records, record))


def lookup_record(
    snapshot: ProvenanceRegistrySnapshot,
    artifact_id: str,
    version: str,
) -> ArtifactProvenanceRecord | None:
    """Return one exact artifact-version record or None when absent."""
    if type(snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("snapshot must be ProvenanceRegistrySnapshot")
    _non_empty(artifact_id, "artifact_id")
    _non_empty(version, "version")

    return next(
        (
            record
            for record in snapshot.records
            if record.artifact.artifact_id == artifact_id
            and record.artifact.version == version
        ),
        None,
    )


def contains_reference(
    snapshot: ProvenanceRegistrySnapshot,
    artifact: ArtifactReference,
) -> bool:
    """Return whether one exact artifact reference exists in the snapshot."""
    if type(snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("snapshot must be ProvenanceRegistrySnapshot")
    if type(artifact) is not ArtifactReference:
        raise TypeError("artifact must be ArtifactReference")
    return any(record.artifact == artifact for record in snapshot.records)


def list_artifact_versions(
    snapshot: ProvenanceRegistrySnapshot,
    artifact_id: str,
) -> tuple[ArtifactProvenanceRecord, ...]:
    """Return all registered versions for one stable artifact identity."""
    if type(snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("snapshot must be ProvenanceRegistrySnapshot")
    _non_empty(artifact_id, "artifact_id")
    return tuple(
        record
        for record in snapshot.records
        if record.artifact.artifact_id == artifact_id
    )


def list_by_admission_state(
    snapshot: ProvenanceRegistrySnapshot,
    admission_state: ArtifactAdmissionState,
) -> tuple[ArtifactProvenanceRecord, ...]:
    """Return records matching one explicit provenance admission state."""
    if type(snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("snapshot must be ProvenanceRegistrySnapshot")
    if type(admission_state) is not ArtifactAdmissionState:
        raise TypeError("admission_state must be ArtifactAdmissionState")
    return tuple(
        record
        for record in snapshot.records
        if record.admission_state is admission_state
    )
