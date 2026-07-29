"""Frozen SATCOM provenance linkage for Issue #9D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.provenance.attribution import (
    AttributionSnapshot,
    CitationRecord,
    EvidenceUseKind,
    EvidenceUseRecord,
    RetrievedEvidenceRecord,
    build_attribution_snapshot,
)
from mh370_inverse_inference.provenance.models import (
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    TransformationStep,
    ValidationReportRecord,
)
from mh370_inverse_inference.provenance.registry import (
    ProvenanceRegistrySnapshot,
    build_registry_snapshot,
    contains_reference,
)

SATCOM_LINKAGE_CONTRACT_VERSION = "SATCOM-PROVENANCE-LINKAGE-1"
SEVENTH_ARC_VALIDATION_CONTEXT_ID = "mh370-seventh-arc-l0.4-validation-v1"
SEVENTH_ARC_VALIDATION_MODEL_VERSION = "l0.4-wgs84-v1"
SEVENTH_ARC_VALIDATION_CONFIGURATION_ID = "sequence-index-aligned-geodesic-v1"

SEVENTH_ARC_TRANSFORM_REFERENCE = ArtifactReference(
    artifact_id="mh370-seventh-arc-bto-wgs84-transform",
    version="v1",
    sha256="4142c33134df8704a466e037b0e1cb065116daea06b74307a986274509f2db21",
)
SEVENTH_ARC_SAMPLING_REFERENCE = ArtifactReference(
    artifact_id="mh370-seventh-arc-canonical-fixture-sampling",
    version="v1",
    sha256="1974f6c5e4be64b211248a34fecbf9d51aa74a9e68e03081a20e5aae4b1a8732",
)
SEVENTH_ARC_FIXTURE_REFERENCE = ArtifactReference(
    artifact_id="mh370-seventh-arc-published-bto",
    version="v1",
    sha256="3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7",
)
SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE = ArtifactReference(
    artifact_id="mh370-seventh-arc-l0.4-validation-output",
    version="v1",
    sha256="6d4b73fd19afaf3aabec46520551be9d05ab89aa25db11126cad747103452982",
)


@dataclass(frozen=True, slots=True)
class SATCOMProvenanceLinkage:
    """Exact registry, validation, and attribution linkage for L0.4."""

    registry_snapshot: ProvenanceRegistrySnapshot
    validation_report: ValidationReportRecord
    attribution_snapshot: AttributionSnapshot
    contract_version: str = SATCOM_LINKAGE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.registry_snapshot) is not ProvenanceRegistrySnapshot:
            raise TypeError("registry_snapshot must be ProvenanceRegistrySnapshot")
        if type(self.validation_report) is not ValidationReportRecord:
            raise TypeError("validation_report must be ValidationReportRecord")
        if type(self.attribution_snapshot) is not AttributionSnapshot:
            raise TypeError("attribution_snapshot must be AttributionSnapshot")
        expected_version = SATCOM_LINKAGE_CONTRACT_VERSION
        if self.contract_version != expected_version:
            raise ValueError(f"contract_version must be {expected_version}")
        if not contains_reference(
            self.registry_snapshot,
            SEVENTH_ARC_FIXTURE_REFERENCE,
        ):
            raise ValueError("registry must contain the exact seventh-arc fixture")
        if not contains_reference(
            self.registry_snapshot,
            SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
        ):
            raise ValueError("registry must contain the exact L0.4 output")
        if self.validation_report.inputs != (SEVENTH_ARC_FIXTURE_REFERENCE,):
            raise ValueError("validation report must reference the exact fixture")
        if self.validation_report.output != SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE:
            raise ValueError("validation report must reference the exact output")
        if (
            self.attribution_snapshot.provenance_snapshot_sha256
            != self.registry_snapshot.snapshot_sha256
        ):
            raise ValueError("attribution must bind to the exact registry snapshot")

    def to_payload(self) -> dict[str, Any]:
        """Return the deterministic linkage payload."""
        return {
            "attribution_snapshot": self.attribution_snapshot.to_payload(),
            "contract_version": self.contract_version,
            "registry_snapshot": self.registry_snapshot.to_payload(),
            "validation_report": self.validation_report.to_payload(),
        }


def _fixture_record() -> ArtifactProvenanceRecord:
    return ArtifactProvenanceRecord(
        artifact=SEVENTH_ARC_FIXTURE_REFERENCE,
        kind=ArtifactKind.DERIVED,
        admission_state=ArtifactAdmissionState.ADMITTED,
        source=None,
        transformation_history=(
            TransformationStep(
                step_index=0,
                operation="freeze_canonical_seventh_arc_fixture",
                inputs=(
                    SEVENTH_ARC_TRANSFORM_REFERENCE,
                    SEVENTH_ARC_SAMPLING_REFERENCE,
                ),
                output=SEVENTH_ARC_FIXTURE_REFERENCE,
                implementation_reference=(
                    "data/satcom/published/"
                    "seventh_arc_canonical_fixture_sampling_v1.yaml"
                ),
                configuration_id="seventh-arc-canonical-fixture-sampling-v1",
            ),
        ),
        uncertainty_notes=(
            "Coordinates are rounded to the frozen fixture precision.",
        ),
        limitations=(
            "Derived validation reference; not a directly published path.",
            "Not a trajectory, endpoint, search area, or crash-location claim.",
        ),
    )


def _validation_output_record() -> ArtifactProvenanceRecord:
    return ArtifactProvenanceRecord(
        artifact=SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
        kind=ArtifactKind.VALIDATION,
        admission_state=ArtifactAdmissionState.ADMITTED,
        source=None,
        transformation_history=(
            TransformationStep(
                step_index=0,
                operation="compare_and_serialize_published_bto_benchmark",
                inputs=(SEVENTH_ARC_FIXTURE_REFERENCE,),
                output=SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
                implementation_reference=(
                    "src/mh370_inverse_inference/satcom/validation.py:"
                    "compare_published_bto_benchmark+"
                    "serialize_bto_validation_result_json"
                ),
                configuration_id=SEVENTH_ARC_VALIDATION_CONFIGURATION_ID,
            ),
        ),
        uncertainty_notes=(
            "Reported deviations are WGS84 ellipsoidal surface distances.",
        ),
        limitations=(
            "Validates deterministic geometry only.",
            "Does not perform BFO, dynamics, inference, or ranking.",
        ),
    )


def build_admitted_seventh_arc_l04_linkage() -> SATCOMProvenanceLinkage:
    """Build the frozen #9D linkage without regenerating either artifact."""
    registry_snapshot = build_registry_snapshot(
        (_fixture_record(), _validation_output_record())
    )
    validation_report = ValidationReportRecord(
        validation_id="mh370-seventh-arc-l0.4-validation",
        validation_version="v1",
        inputs=(SEVENTH_ARC_FIXTURE_REFERENCE,),
        output=SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
        model_version=SEVENTH_ARC_VALIDATION_MODEL_VERSION,
        configuration_id=SEVENTH_ARC_VALIDATION_CONFIGURATION_ID,
    )
    attribution_snapshot = build_attribution_snapshot(
        registry_snapshot,
        retrieved=(
            RetrievedEvidenceRecord(
                retrieval_id="mh370-seventh-arc-fixture-retrieval-v1",
                artifact=SEVENTH_ARC_FIXTURE_REFERENCE,
                context_id=SEVENTH_ARC_VALIDATION_CONTEXT_ID,
            ),
        ),
        citations=(
            CitationRecord(
                citation_id="mh370-seventh-arc-fixture-citation-v1",
                artifact=SEVENTH_ARC_FIXTURE_REFERENCE,
                context_id=SEVENTH_ARC_VALIDATION_CONTEXT_ID,
                locator="$.fixture_sha256",
            ),
        ),
        uses=(
            EvidenceUseRecord(
                use_id="mh370-seventh-arc-fixture-use-v1",
                artifact=SEVENTH_ARC_FIXTURE_REFERENCE,
                context_id=SEVENTH_ARC_VALIDATION_CONTEXT_ID,
                use_kind=EvidenceUseKind.COMPUTATION,
                operation_reference=(
                    "src/mh370_inverse_inference/satcom/validation.py:"
                    "compare_published_bto_benchmark"
                ),
            ),
        ),
    )
    return SATCOMProvenanceLinkage(
        registry_snapshot=registry_snapshot,
        validation_report=validation_report,
        attribution_snapshot=attribution_snapshot,
    )
