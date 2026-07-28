"""Tests for immutable repository-level provenance contracts."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import (
    PROVENANCE_CONTRACT_VERSION,
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    SourceReference,
    TransformationStep,
    ValidationReportRecord,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _source() -> SourceReference:
    return SourceReference(
        source_id="source-a",
        publisher="Example Publisher",
        title="Example Source",
        reference_uri="https://example.invalid/source-a",
        retrieved_at_utc="2026-07-28T00:00:00Z",
        licence_or_terms="Documented source terms",
        content_hash=HASH_A,
    )


def _source_artifact() -> ArtifactReference:
    return ArtifactReference(
        artifact_id="artifact-source-a",
        version="1",
        sha256=HASH_A,
    )


def _derived_artifact() -> ArtifactReference:
    return ArtifactReference(
        artifact_id="artifact-derived-b",
        version="1",
        sha256=HASH_B,
    )


def _transformation() -> TransformationStep:
    return TransformationStep(
        step_index=0,
        operation="deterministic_transform",
        inputs=(_source_artifact(),),
        output=_derived_artifact(),
        implementation_reference="src/example.py:transform",
        configuration_id="example-transform-v1",
    )


def test_source_artifact_contract_is_immutable_and_canonical() -> None:
    record = ArtifactProvenanceRecord(
        artifact=_source_artifact(),
        kind=ArtifactKind.SOURCE,
        admission_state=ArtifactAdmissionState.ADMITTED,
        source=_source(),
        transformation_history=(),
        uncertainty_notes=("Source uncertainty retained as published.",),
        limitations=("No derived interpretation is encoded here.",),
    )

    assert record.contract_version == PROVENANCE_CONTRACT_VERSION
    assert record.to_payload()["admission_state"] == "ADMITTED"
    assert record.to_payload()["artifact"]["sha256"] == HASH_A
    with pytest.raises(FrozenInstanceError):
        record.kind = ArtifactKind.DERIVED  # type: ignore[misc]


def test_source_artifact_requires_matching_source_hash_and_no_transform() -> None:
    wrong_artifact = ArtifactReference(
        artifact_id="artifact-source-a",
        version="1",
        sha256=HASH_B,
    )
    with pytest.raises(ValueError, match="hash must match"):
        ArtifactProvenanceRecord(
            artifact=wrong_artifact,
            kind=ArtifactKind.SOURCE,
            admission_state=ArtifactAdmissionState.VERIFIED,
            source=_source(),
            transformation_history=(),
            uncertainty_notes=(),
            limitations=(),
        )

    with pytest.raises(ValueError, match="cannot include transformation_history"):
        ArtifactProvenanceRecord(
            artifact=_source_artifact(),
            kind=ArtifactKind.SOURCE,
            admission_state=ArtifactAdmissionState.VERIFIED,
            source=_source(),
            transformation_history=(_transformation(),),
            uncertainty_notes=(),
            limitations=(),
        )


def test_derived_artifact_requires_ordered_history_ending_at_artifact() -> None:
    record = ArtifactProvenanceRecord(
        artifact=_derived_artifact(),
        kind=ArtifactKind.DERIVED,
        admission_state=ArtifactAdmissionState.PROPOSED,
        source=_source(),
        transformation_history=(_transformation(),),
        uncertainty_notes=("Transformation uncertainty is explicit.",),
        limitations=("This record does not establish scientific authority.",),
    )

    assert record.transformation_history[0].step_index == 0
    assert record.transformation_history[0].output == record.artifact

    with pytest.raises(ValueError, match="require transformation_history"):
        ArtifactProvenanceRecord(
            artifact=_derived_artifact(),
            kind=ArtifactKind.DERIVED,
            admission_state=ArtifactAdmissionState.PROPOSED,
            source=_source(),
            transformation_history=(),
            uncertainty_notes=(),
            limitations=(),
        )

    wrong_index = TransformationStep(
        step_index=1,
        operation="deterministic_transform",
        inputs=(_source_artifact(),),
        output=_derived_artifact(),
        implementation_reference="src/example.py:transform",
        configuration_id="example-transform-v1",
    )
    with pytest.raises(ValueError, match="contiguous ordered"):
        ArtifactProvenanceRecord(
            artifact=_derived_artifact(),
            kind=ArtifactKind.DERIVED,
            admission_state=ArtifactAdmissionState.PROPOSED,
            source=_source(),
            transformation_history=(wrong_index,),
            uncertainty_notes=(),
            limitations=(),
        )


def test_superseded_state_requires_distinct_replacement_reference() -> None:
    replacement = ArtifactReference(
        artifact_id="artifact-derived-b",
        version="2",
        sha256=HASH_C,
    )
    record = ArtifactProvenanceRecord(
        artifact=_derived_artifact(),
        kind=ArtifactKind.DERIVED,
        admission_state=ArtifactAdmissionState.SUPERSEDED,
        source=_source(),
        transformation_history=(_transformation(),),
        uncertainty_notes=(),
        limitations=(),
        superseded_by=replacement,
    )

    assert record.superseded_by == replacement

    with pytest.raises(ValueError, match="requires superseded_by"):
        ArtifactProvenanceRecord(
            artifact=_derived_artifact(),
            kind=ArtifactKind.DERIVED,
            admission_state=ArtifactAdmissionState.SUPERSEDED,
            source=_source(),
            transformation_history=(_transformation(),),
            uncertainty_notes=(),
            limitations=(),
        )


def test_validation_report_links_exact_input_and_output_versions() -> None:
    report = ValidationReportRecord(
        validation_id="validation-example",
        validation_version="1",
        inputs=(_source_artifact(),),
        output=_derived_artifact(),
        model_version="model-v1",
        configuration_id="configuration-v1",
    )

    payload = report.to_payload()
    assert payload["validation_id"] == "validation-example"
    assert payload["inputs"] == [_source_artifact().to_payload()]
    assert payload["output"] == _derived_artifact().to_payload()

    with pytest.raises(ValueError, match="duplicate artifact references"):
        ValidationReportRecord(
            validation_id="validation-example",
            validation_version="1",
            inputs=(_source_artifact(), _source_artifact()),
            output=_derived_artifact(),
            model_version="model-v1",
            configuration_id="configuration-v1",
        )


def test_contracts_reject_noncanonical_hashes_and_timestamps() -> None:
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        ArtifactReference(
            artifact_id="artifact-a",
            version="1",
            sha256="A" * 64,
        )

    with pytest.raises(ValueError, match="canonical UTC Z notation"):
        SourceReference(
            source_id="source-a",
            publisher="Example Publisher",
            title="Example Source",
            reference_uri="https://example.invalid/source-a",
            retrieved_at_utc="2026-07-28T00:00:00+00:00",
            licence_or_terms="Documented source terms",
            content_hash=HASH_A,
        )
