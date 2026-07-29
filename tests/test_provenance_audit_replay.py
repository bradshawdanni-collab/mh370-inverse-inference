"""Tests for the Issue #9E provenance audit and deterministic replay."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.provenance import (
    SEVENTH_ARC_FIXTURE_REFERENCE,
    SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    AuditStatus,
    DeterministicReplayReport,
    ProvenanceAuditCheck,
    audit_satcom_provenance_linkage,
    build_admitted_seventh_arc_l04_linkage,
    build_issue_9_full_audit,
    build_registry_snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "mh370_inverse_inference"
    / "provenance"
    / "audit.py"
)
SATCOM_LINKAGE_PATH = (
    REPO_ROOT
    / "src"
    / "mh370_inverse_inference"
    / "provenance"
    / "satcom_linkage.py"
)


def test_audit_passes_for_frozen_chain() -> None:
    report = build_issue_9_full_audit()

    assert report.overall_result is AuditStatus.PASS
    assert all(check.status is AuditStatus.PASS for check in report.checks)
    assert report.to_payload()["validation_linkage"]["sample_count"] == 176


def test_repeated_replay_is_identical() -> None:
    first = build_issue_9_full_audit()
    second = build_issue_9_full_audit()

    assert first == second
    assert first.replay.final_replay_sha256 == second.replay.final_replay_sha256
    assert first.to_payload() == second.to_payload()


def test_registry_record_order_does_not_change_replay() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    reversed_registry = build_registry_snapshot(
        tuple(reversed(linkage.registry_snapshot.records))
    )
    rebuilt = replace(linkage, registry_snapshot=reversed_registry)

    assert audit_satcom_provenance_linkage(rebuilt).replay == (
        audit_satcom_provenance_linkage(linkage).replay
    )


def test_wrong_fixture_digest_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    wrong_fixture = ArtifactReference(
        artifact_id=SEVENTH_ARC_FIXTURE_REFERENCE.artifact_id,
        version=SEVENTH_ARC_FIXTURE_REFERENCE.version,
        sha256="0" * 64,
    )
    records = tuple(
        replace(record, artifact=wrong_fixture)
        if record.artifact == SEVENTH_ARC_FIXTURE_REFERENCE
        else record
        for record in linkage.registry_snapshot.records
    )

    with pytest.raises(ValueError):
        replace(linkage, registry_snapshot=build_registry_snapshot(records))


def test_wrong_validation_output_digest_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    wrong_output = ArtifactReference(
        artifact_id=SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.artifact_id,
        version=SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.version,
        sha256="0" * 64,
    )

    with pytest.raises(ValueError, match="exact output"):
        replace(
            linkage,
            validation_report=replace(linkage.validation_report, output=wrong_output),
        )


def test_missing_registry_record_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    fixture_only = build_registry_snapshot(
        tuple(
            record
            for record in linkage.registry_snapshot.records
            if record.artifact == SEVENTH_ARC_FIXTURE_REFERENCE
        )
    )

    with pytest.raises(ValueError, match="exact L0.4 output"):
        replace(linkage, registry_snapshot=fixture_only)


def test_non_admitted_used_evidence_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    records = tuple(
        replace(record, admission_state=ArtifactAdmissionState.VERIFIED)
        if record.artifact == SEVENTH_ARC_FIXTURE_REFERENCE
        else record
        for record in linkage.registry_snapshot.records
    )
    registry = build_registry_snapshot(records)

    with pytest.raises(ValueError, match="exact registry snapshot"):
        replace(linkage, registry_snapshot=registry)


def test_wrong_validation_input_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    wrong_input = ArtifactReference(
        artifact_id="wrong-input",
        version="v1",
        sha256="0" * 64,
    )

    with pytest.raises(ValueError, match="exact fixture"):
        replace(
            linkage,
            validation_report=replace(linkage.validation_report, inputs=(wrong_input,)),
        )


def test_wrong_registry_snapshot_binding_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    attribution = replace(
        linkage.attribution_snapshot,
        provenance_snapshot_sha256="0" * 64,
    )

    with pytest.raises(ValueError):
        replace(linkage, attribution_snapshot=attribution)


def test_wrong_attribution_snapshot_hash_fails_closed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()

    with pytest.raises(ValueError, match="snapshot_sha256"):
        replace(linkage.attribution_snapshot, snapshot_sha256="0" * 64)


def test_modified_replay_step_fails_closed() -> None:
    report = build_issue_9_full_audit()
    changed = replace(report.replay.steps[0], payload_sha256="0" * 64)
    steps = (changed, *report.replay.steps[1:])

    with pytest.raises(ValueError, match="final_replay_sha256"):
        DeterministicReplayReport(
            steps=steps,
            final_replay_sha256=report.replay.final_replay_sha256,
        )


def test_audit_records_are_immutable() -> None:
    check = ProvenanceAuditCheck("immutable", AuditStatus.PASS, "Frozen record.")

    with pytest.raises(FrozenInstanceError):
        check.detail = "changed"  # type: ignore[misc]


def test_replay_hash_matches_canonical_steps() -> None:
    report = build_issue_9_full_audit()

    assert report.replay.final_replay_sha256 == sha256_payload(
        [step.to_payload() for step in report.replay.steps]
    )


def test_no_satcom_artifact_regeneration_occurs() -> None:
    source = AUDIT_MODULE_PATH.read_text(encoding="utf-8")
    linkage_source = SATCOM_LINKAGE_PATH.read_text(encoding="utf-8")

    for forbidden in (
        "generate_surface_locus",
        "load_admitted_seventh_arc_benchmark",
        "serialize_bto_validation_result_json(",
    ):
        assert forbidden not in source
        assert forbidden not in linkage_source


def test_fixture_and_output_inventory_is_complete() -> None:
    report = build_issue_9_full_audit().to_payload()

    fixture = report["artifact_references"]["fixture"]
    output = report["artifact_references"]["validation_output"]
    assert fixture["artifact_id"] == SEVENTH_ARC_FIXTURE_REFERENCE.artifact_id
    assert fixture["sha256"] == SEVENTH_ARC_FIXTURE_REFERENCE.sha256
    assert output["artifact_id"] == SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.artifact_id
    assert output["sha256"] == SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.sha256


def test_artifact_kinds_remain_governed() -> None:
    linkage = build_admitted_seventh_arc_l04_linkage()
    records = {record.artifact: record for record in linkage.registry_snapshot.records}

    fixture_record: ArtifactProvenanceRecord = records[SEVENTH_ARC_FIXTURE_REFERENCE]
    output_record: ArtifactProvenanceRecord = records[
        SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE
    ]
    assert fixture_record.kind is ArtifactKind.DERIVED
    assert output_record.kind is ArtifactKind.VALIDATION
