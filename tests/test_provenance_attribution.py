"""Tests for Issue #9C attribution and evidence-use linkage."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import (
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    CitationRecord,
    EvidenceUseKind,
    EvidenceUseRecord,
    RetrievedEvidenceRecord,
    SourceReference,
    build_attribution_snapshot,
    build_registry_snapshot,
    citations_for_artifact,
    compute_sha256,
    retrieved_for_artifact,
    uses_for_artifact,
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
        retrieved_at_utc="2026-07-29T00:00:00Z",
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


def test_attribution_snapshot_separates_retrieved_cited_and_used_records() -> None:
    source = _source_record("artifact-a", "v1", b"source")
    registry = build_registry_snapshot((source,))
    retrieved = RetrievedEvidenceRecord(
        retrieval_id="retrieval-1",
        artifact=source.artifact,
        context_id="review-context",
    )
    citation = CitationRecord(
        citation_id="citation-1",
        artifact=source.artifact,
        context_id="report-context",
        locator="section-2",
    )
    use = EvidenceUseRecord(
        use_id="use-1",
        artifact=source.artifact,
        context_id="validation-context",
        use_kind=EvidenceUseKind.COMPUTATION,
        operation_reference="validation:model-v1/config-v1",
    )

    snapshot = build_attribution_snapshot(
        registry,
        retrieved=(retrieved,),
        citations=(citation,),
        uses=(use,),
    )

    assert snapshot.retrieved == (retrieved,)
    assert snapshot.citations == (citation,)
    assert snapshot.uses == (use,)
    assert retrieved.to_payload()["record_type"] == "RETRIEVED"
    assert citation.to_payload()["record_type"] == "CITED"
    assert use.to_payload()["record_type"] == "USED"
    assert snapshot.provenance_snapshot_sha256 == registry.snapshot_sha256


def test_attribution_snapshot_is_deterministic_under_input_reordering() -> None:
    first = _source_record("artifact-a", "v1", b"a")
    second = _source_record("artifact-b", "v1", b"b")
    registry = build_registry_snapshot((first, second))
    citation_a = CitationRecord(
        citation_id="citation-a",
        artifact=first.artifact,
        context_id="report",
        locator="a",
    )
    citation_b = CitationRecord(
        citation_id="citation-b",
        artifact=second.artifact,
        context_id="report",
        locator="b",
    )

    forward = build_attribution_snapshot(
        registry,
        citations=(citation_a, citation_b),
    )
    reverse = build_attribution_snapshot(
        registry,
        citations=(citation_b, citation_a),
    )

    assert forward == reverse
    assert forward.snapshot_sha256 == reverse.snapshot_sha256
    assert forward.to_payload() == reverse.to_payload()


def test_citation_does_not_imply_admission_or_evidence_use() -> None:
    rejected = _source_record(
        "candidate-source",
        "v1",
        b"candidate",
        admission_state=ArtifactAdmissionState.REJECTED,
    )
    registry = build_registry_snapshot((rejected,))
    citation = CitationRecord(
        citation_id="citation-candidate",
        artifact=rejected.artifact,
        context_id="candidate-discussion",
        locator="candidate-reference",
    )

    snapshot = build_attribution_snapshot(registry, citations=(citation,))

    assert snapshot.citations == (citation,)
    assert snapshot.retrieved == ()
    assert snapshot.uses == ()


def test_evidence_use_requires_exact_admitted_artifact() -> None:
    verified = _source_record(
        "artifact-a",
        "v1",
        b"verified",
        admission_state=ArtifactAdmissionState.VERIFIED,
    )
    registry = build_registry_snapshot((verified,))
    use = EvidenceUseRecord(
        use_id="use-verified",
        artifact=verified.artifact,
        context_id="calculation",
        use_kind=EvidenceUseKind.COMPUTATION,
        operation_reference="model-v1",
    )

    with pytest.raises(ValueError, match="ADMITTED"):
        build_attribution_snapshot(registry, uses=(use,))


def test_attribution_rejects_unregistered_or_hash_mismatched_reference() -> None:
    source = _source_record("artifact-a", "v1", b"source")
    registry = build_registry_snapshot((source,))
    wrong_reference = ArtifactReference(
        artifact_id=source.artifact.artifact_id,
        version=source.artifact.version,
        sha256="0" * 64,
    )
    citation = CitationRecord(
        citation_id="citation-wrong-hash",
        artifact=wrong_reference,
        context_id="report",
        locator="section-1",
    )

    with pytest.raises(ValueError, match="exact registered reference"):
        build_attribution_snapshot(registry, citations=(citation,))


def test_attribution_record_identifiers_are_globally_unique() -> None:
    source = _source_record("artifact-a", "v1", b"source")
    registry = build_registry_snapshot((source,))
    retrieved = RetrievedEvidenceRecord(
        retrieval_id="same-id",
        artifact=source.artifact,
        context_id="review",
    )
    citation = CitationRecord(
        citation_id="same-id",
        artifact=source.artifact,
        context_id="report",
        locator="section-1",
    )

    with pytest.raises(ValueError, match="globally unique"):
        build_attribution_snapshot(
            registry,
            retrieved=(retrieved,),
            citations=(citation,),
        )


def test_attribution_queries_require_exact_artifact_reference() -> None:
    source = _source_record("artifact-a", "v1", b"source")
    registry = build_registry_snapshot((source,))
    retrieved = RetrievedEvidenceRecord(
        retrieval_id="retrieval-1",
        artifact=source.artifact,
        context_id="review",
    )
    citation = CitationRecord(
        citation_id="citation-1",
        artifact=source.artifact,
        context_id="report",
        locator="section-1",
    )
    use = EvidenceUseRecord(
        use_id="use-1",
        artifact=source.artifact,
        context_id="calculation",
        use_kind=EvidenceUseKind.JUDGEMENT,
        operation_reference="review-rule-v1",
    )
    snapshot = build_attribution_snapshot(
        registry,
        retrieved=(retrieved,),
        citations=(citation,),
        uses=(use,),
    )

    assert retrieved_for_artifact(snapshot, source.artifact) == (retrieved,)
    assert citations_for_artifact(snapshot, source.artifact) == (citation,)
    assert uses_for_artifact(snapshot, source.artifact) == (use,)


def test_attribution_snapshot_is_immutable_and_detects_hash_tampering() -> None:
    source = _source_record("artifact-a", "v1", b"source")
    registry = build_registry_snapshot((source,))
    snapshot = build_attribution_snapshot(registry)

    with pytest.raises(FrozenInstanceError):
        snapshot.snapshot_sha256 = "0" * 64  # type: ignore[misc]

    with pytest.raises(ValueError, match="does not match canonical attribution"):
        type(snapshot)(
            provenance_snapshot_sha256=snapshot.provenance_snapshot_sha256,
            retrieved=snapshot.retrieved,
            citations=snapshot.citations,
            uses=snapshot.uses,
            snapshot_sha256="0" * 64,
        )
