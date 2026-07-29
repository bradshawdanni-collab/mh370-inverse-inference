"""Tests for the frozen Issue #9D SATCOM provenance linkage."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from mh370_inverse_inference.provenance import (
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactReference,
    EvidenceUseKind,
    SATCOMProvenanceLinkage,
    SEVENTH_ARC_FIXTURE_REFERENCE,
    SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
    build_admitted_seventh_arc_l04_linkage,
    citations_for_artifact,
    contains_reference,
    retrieved_for_artifact,
    uses_for_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPO_ROOT / "data" / "satcom" / "published" / "benchmark_fixture.csv"
)
LINKAGE_MANIFEST_PATH = (
    REPO_ROOT
    / "data"
    / "satcom"
    / "published"
    / "seventh_arc_l04_provenance_linkage_v1.yaml"
)
VALIDATION_OUTPUT_PATH = (
    REPO_ROOT
    / "data"
    / "satcom"
    / "published"
    / "seventh_arc_l04_validation_result_v1.json"
)


def test_fixture_and_validation_output_identities_are_frozen() -> None:
    fixture_bytes = FIXTURE_PATH.read_bytes()
    manifest = LINKAGE_MANIFEST_PATH.read_text(encoding="utf-8")

    assert hashlib.sha256(fixture_bytes).hexdigest() == (
        SEVENTH_ARC_FIXTURE_REFERENCE.sha256
    )
    assert SEVENTH_ARC_FIXTURE_REFERENCE.sha256 in manifest
    assert SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.sha256 in manifest
    assert "fixture_regenerated: false" in manifest
    assert "validation_output_regenerated: false" in manifest
    assert "validation_output_bytes_vendored: false" in manifest
    assert not VALIDATION_OUTPUT_PATH.exists()


def test_linkage_builds_exact_registry_and_validation_report() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()

    assert contains_reference(
        linkage.registry_snapshot,
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )
    assert contains_reference(
        linkage.registry_snapshot,
        SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
    )
    assert linkage.validation_report.inputs == (
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )
    assert (
        linkage.validation_report.output
        == SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE
    )
    assert linkage.validation_report.model_version == "l0.4-wgs84-v1"
    assert linkage.validation_report.configuration_id == (
        "sequence-index-aligned-geodesic-v1"
    )


def test_linkage_preserves_admission_and_artifact_kinds() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    records = {
        record.artifact: record for record in linkage.registry_snapshot.records
    }

    fixture_record = records[SEVENTH_ARC_FIXTURE_REFERENCE]
    output_record = records[SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE]

    assert fixture_record.kind is ArtifactKind.DERIVED
    assert fixture_record.admission_state is ArtifactAdmissionState.ADMITTED
    assert output_record.kind is ArtifactKind.VALIDATION
    assert output_record.admission_state is ArtifactAdmissionState.ADMITTED
    assert output_record.transformation_history[0].inputs == (
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )


def test_linkage_separates_retrieved_cited_and_used_evidence() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    attribution = linkage.attribution_snapshot

    retrieved = retrieved_for_artifact(
        attribution,
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )
    citations = citations_for_artifact(
        attribution,
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )
    uses = uses_for_artifact(
        attribution,
        SEVENTH_ARC_FIXTURE_REFERENCE,
    )

    assert len(retrieved) == 1
    assert len(citations) == 1
    assert len(uses) == 1
    assert citations[0].locator == "$.fixture_sha256"
    assert uses[0].use_kind is EvidenceUseKind.COMPUTATION
    assert (
        attribution.provenance_snapshot_sha256
        == linkage.registry_snapshot.snapshot_sha256
    )


def test_linkage_payload_is_deterministic() -> None:
    first = build_admitted_seventh_arc_l04_linkage()
    second = build_admitted_seventh_arc_l04_linkage()

    assert first == second
    assert first.to_payload() == second.to_payload()


def test_linkage_rejects_mismatched_validation_output() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    wrong_output = ArtifactReference(
        artifact_id="mh370-seventh-arc-l0.4-validation-output",
        version="v1",
        sha256="0" * 64,
    )
    bad_report = replace(linkage.validation_report, output=wrong_output)

    with pytest.raises(ValueError, match="exact output"):
        SATCOMProvenanceLinkage(
            registry_snapshot=linkage.registry_snapshot,
            validation_report=bad_report,
            attribution_snapshot=linkage.attribution_snapshot,
        )


def test_linkage_module_does_not_regenerate_satcom_artifacts() -> None:
    module_path = (
        REPO_ROOT
        / "src"
        / "mh370_inverse_inference"
        / "provenance"
        / "satcom_linkage.py"
    )
    source = module_path.read_text(encoding="utf-8")

    assert "generate_surface_locus" not in source
    assert "serialize_bto_validation_result_json(" not in source
    assert "load_admitted_seventh_arc_benchmark" not in source
