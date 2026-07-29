"""Deterministic attribution and evidence-use linkage for Issue #9C."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.provenance.models import (
    ArtifactAdmissionState,
    ArtifactProvenanceRecord,
    ArtifactReference,
)
from mh370_inverse_inference.provenance.registry import (
    ProvenanceRegistrySnapshot,
    lookup_record,
)

ATTRIBUTION_CONTRACT_VERSION = "PROVENANCE-ATTRIBUTION-1"


class EvidenceUseKind(StrEnum):
    """Explicit downstream ways in which evidence can affect an outcome."""

    COMPUTATION = "COMPUTATION"
    JUDGEMENT = "JUDGEMENT"


def _non_empty(value: str, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")
    return value


def _artifact_reference(value: ArtifactReference, name: str) -> ArtifactReference:
    if type(value) is not ArtifactReference:
        raise TypeError(f"{name} must be ArtifactReference")
    return value


@dataclass(frozen=True, slots=True)
class RetrievedEvidenceRecord:
    """Explicit record that one exact artifact was available to a context."""

    retrieval_id: str
    artifact: ArtifactReference
    context_id: str
    contract_version: str = ATTRIBUTION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.retrieval_id, "retrieval_id")
        _artifact_reference(self.artifact, "artifact")
        _non_empty(self.context_id, "context_id")
        if self.contract_version != ATTRIBUTION_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {ATTRIBUTION_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical retrieved-evidence payload."""
        return {
            "artifact": self.artifact.to_payload(),
            "context_id": self.context_id,
            "contract_version": self.contract_version,
            "record_type": "RETRIEVED",
            "retrieval_id": self.retrieval_id,
        }


@dataclass(frozen=True, slots=True)
class CitationRecord:
    """Explicit citation of one exact artifact in a named output context."""

    citation_id: str
    artifact: ArtifactReference
    context_id: str
    locator: str
    contract_version: str = ATTRIBUTION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.citation_id, "citation_id")
        _artifact_reference(self.artifact, "artifact")
        _non_empty(self.context_id, "context_id")
        _non_empty(self.locator, "locator")
        if self.contract_version != ATTRIBUTION_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {ATTRIBUTION_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical citation payload."""
        return {
            "artifact": self.artifact.to_payload(),
            "citation_id": self.citation_id,
            "context_id": self.context_id,
            "contract_version": self.contract_version,
            "locator": self.locator,
            "record_type": "CITED",
        }


@dataclass(frozen=True, slots=True)
class EvidenceUseRecord:
    """Explicit record that one exact admitted artifact affected an outcome."""

    use_id: str
    artifact: ArtifactReference
    context_id: str
    use_kind: EvidenceUseKind
    operation_reference: str
    contract_version: str = ATTRIBUTION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.use_id, "use_id")
        _artifact_reference(self.artifact, "artifact")
        _non_empty(self.context_id, "context_id")
        if type(self.use_kind) is not EvidenceUseKind:
            raise TypeError("use_kind must be EvidenceUseKind")
        _non_empty(self.operation_reference, "operation_reference")
        if self.contract_version != ATTRIBUTION_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {ATTRIBUTION_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical evidence-use payload."""
        return {
            "artifact": self.artifact.to_payload(),
            "context_id": self.context_id,
            "contract_version": self.contract_version,
            "operation_reference": self.operation_reference,
            "record_type": "USED",
            "use_id": self.use_id,
            "use_kind": self.use_kind.value,
        }


def attribution_identity_payload(
    *,
    provenance_snapshot_sha256: str,
    retrieved: tuple[RetrievedEvidenceRecord, ...],
    citations: tuple[CitationRecord, ...],
    uses: tuple[EvidenceUseRecord, ...],
) -> dict[str, Any]:
    """Return the canonical identity payload for one attribution snapshot."""
    return {
        "citations": [record.to_payload() for record in citations],
        "contract_version": ATTRIBUTION_CONTRACT_VERSION,
        "provenance_snapshot_sha256": provenance_snapshot_sha256,
        "retrieved": [record.to_payload() for record in retrieved],
        "uses": [record.to_payload() for record in uses],
    }


@dataclass(frozen=True, slots=True)
class AttributionSnapshot:
    """Immutable separation of retrieved, cited, and used evidence."""

    provenance_snapshot_sha256: str
    retrieved: tuple[RetrievedEvidenceRecord, ...]
    citations: tuple[CitationRecord, ...]
    uses: tuple[EvidenceUseRecord, ...]
    snapshot_sha256: str
    contract_version: str = ATTRIBUTION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.provenance_snapshot_sha256) is not str:
            raise TypeError("provenance_snapshot_sha256 must be str")
        if len(self.provenance_snapshot_sha256) != 64:
            raise ValueError("provenance_snapshot_sha256 must be a SHA-256 digest")
        if type(self.retrieved) is not tuple:
            raise TypeError("retrieved must be tuple")
        if type(self.citations) is not tuple:
            raise TypeError("citations must be tuple")
        if type(self.uses) is not tuple:
            raise TypeError("uses must be tuple")
        if any(type(record) is not RetrievedEvidenceRecord for record in self.retrieved):
            raise TypeError("retrieved must contain RetrievedEvidenceRecord values")
        if any(type(record) is not CitationRecord for record in self.citations):
            raise TypeError("citations must contain CitationRecord values")
        if any(type(record) is not EvidenceUseRecord for record in self.uses):
            raise TypeError("uses must contain EvidenceUseRecord values")
        if self.contract_version != ATTRIBUTION_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {ATTRIBUTION_CONTRACT_VERSION}"
            )
        self._validate_order_and_identity()
        expected = sha256_payload(
            attribution_identity_payload(
                provenance_snapshot_sha256=self.provenance_snapshot_sha256,
                retrieved=self.retrieved,
                citations=self.citations,
                uses=self.uses,
            )
        )
        if self.snapshot_sha256 != expected:
            raise ValueError("snapshot_sha256 does not match canonical attribution records")

    def _validate_order_and_identity(self) -> None:
        retrieval_ids = tuple(record.retrieval_id for record in self.retrieved)
        citation_ids = tuple(record.citation_id for record in self.citations)
        use_ids = tuple(record.use_id for record in self.uses)
        if retrieval_ids != tuple(sorted(retrieval_ids)):
            raise ValueError("retrieved records must be ordered by retrieval_id")
        if citation_ids != tuple(sorted(citation_ids)):
            raise ValueError("citation records must be ordered by citation_id")
        if use_ids != tuple(sorted(use_ids)):
            raise ValueError("evidence-use records must be ordered by use_id")
        all_ids = (*retrieval_ids, *citation_ids, *use_ids)
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("attribution record identifiers must be globally unique")

    def to_payload(self) -> dict[str, Any]:
        """Return the deterministic attribution snapshot payload."""
        payload = attribution_identity_payload(
            provenance_snapshot_sha256=self.provenance_snapshot_sha256,
            retrieved=self.retrieved,
            citations=self.citations,
            uses=self.uses,
        )
        return {**payload, "snapshot_sha256": self.snapshot_sha256}


def _registered_record(
    snapshot: ProvenanceRegistrySnapshot,
    artifact: ArtifactReference,
) -> ArtifactProvenanceRecord:
    record = lookup_record(snapshot, artifact.artifact_id, artifact.version)
    if record is None or record.artifact != artifact:
        raise ValueError("attribution artifact must match an exact registered reference")
    return record


def build_attribution_snapshot(
    provenance_snapshot: ProvenanceRegistrySnapshot,
    *,
    retrieved: tuple[RetrievedEvidenceRecord, ...] = (),
    citations: tuple[CitationRecord, ...] = (),
    uses: tuple[EvidenceUseRecord, ...] = (),
) -> AttributionSnapshot:
    """Build an immutable attribution snapshot against one provenance snapshot."""
    if type(provenance_snapshot) is not ProvenanceRegistrySnapshot:
        raise TypeError("provenance_snapshot must be ProvenanceRegistrySnapshot")
    if type(retrieved) is not tuple:
        raise TypeError("retrieved must be tuple")
    if type(citations) is not tuple:
        raise TypeError("citations must be tuple")
    if type(uses) is not tuple:
        raise TypeError("uses must be tuple")

    for record in retrieved:
        if type(record) is not RetrievedEvidenceRecord:
            raise TypeError("retrieved must contain RetrievedEvidenceRecord values")
        _registered_record(provenance_snapshot, record.artifact)
    for record in citations:
        if type(record) is not CitationRecord:
            raise TypeError("citations must contain CitationRecord values")
        _registered_record(provenance_snapshot, record.artifact)
    for record in uses:
        if type(record) is not EvidenceUseRecord:
            raise TypeError("uses must contain EvidenceUseRecord values")
        provenance_record = _registered_record(provenance_snapshot, record.artifact)
        if provenance_record.admission_state is not ArtifactAdmissionState.ADMITTED:
            raise ValueError("used evidence must reference an ADMITTED artifact")

    ordered_retrieved = tuple(sorted(retrieved, key=lambda record: record.retrieval_id))
    ordered_citations = tuple(sorted(citations, key=lambda record: record.citation_id))
    ordered_uses = tuple(sorted(uses, key=lambda record: record.use_id))
    identity = attribution_identity_payload(
        provenance_snapshot_sha256=provenance_snapshot.snapshot_sha256,
        retrieved=ordered_retrieved,
        citations=ordered_citations,
        uses=ordered_uses,
    )
    return AttributionSnapshot(
        provenance_snapshot_sha256=provenance_snapshot.snapshot_sha256,
        retrieved=ordered_retrieved,
        citations=ordered_citations,
        uses=ordered_uses,
        snapshot_sha256=sha256_payload(identity),
    )


def retrieved_for_artifact(
    snapshot: AttributionSnapshot,
    artifact: ArtifactReference,
) -> tuple[RetrievedEvidenceRecord, ...]:
    """Return explicit retrieval records for one exact artifact reference."""
    _artifact_reference(artifact, "artifact")
    return tuple(record for record in snapshot.retrieved if record.artifact == artifact)


def citations_for_artifact(
    snapshot: AttributionSnapshot,
    artifact: ArtifactReference,
) -> tuple[CitationRecord, ...]:
    """Return explicit citation records for one exact artifact reference."""
    _artifact_reference(artifact, "artifact")
    return tuple(record for record in snapshot.citations if record.artifact == artifact)


def uses_for_artifact(
    snapshot: AttributionSnapshot,
    artifact: ArtifactReference,
) -> tuple[EvidenceUseRecord, ...]:
    """Return explicit evidence-use records for one exact artifact reference."""
    _artifact_reference(artifact, "artifact")
    return tuple(record for record in snapshot.uses if record.artifact == artifact)
