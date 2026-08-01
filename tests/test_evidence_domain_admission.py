from __future__ import annotations

from dataclasses import replace

import pytest

from mh370_inverse_inference.evidence.domain_admission import (
    EXCLUSIONS,
    EvidenceAdmissionState,
    EvidenceSource,
    TransformationStep,
    UncertaintyRepresentation,
    ValidationIdentity,
    create_evidence_domain_admission_record,
)


def _source() -> EvidenceSource:
    return EvidenceSource(
        source_id="radar-source",
        source_version="v1",
        citation="Authoritative radar source citation",
        content_hash="a" * 64,
    )


def _transformation() -> TransformationStep:
    return TransformationStep(
        sequence_index=0,
        operation="NORMALIZE_COORDINATES",
        implementation_version="v1",
        parameters_hash="b" * 64,
    )


def _uncertainty() -> UncertaintyRepresentation:
    return UncertaintyRepresentation(
        representation_type="INTERVAL",
        units="nautical_miles",
        lower_bound=0.0,
        upper_bound=10.0,
        method="SOURCE_REPORTED_BOUND",
    )


def _validation(*, disposition: str = "PASS") -> ValidationIdentity:
    return ValidationIdentity(
        report_id="RADAR-VALIDATION-V1",
        report_version="v1",
        report_hash="c" * 64,
        disposition=disposition,
    )


def test_creates_deterministic_admitted_record() -> None:
    record = create_evidence_domain_admission_record(
        domain_id="radar-uncertainty",
        domain_version="v1",
        domain_type="RADAR_UNCERTAINTY",
        sources=(_source(),),
        transformations=(_transformation(),),
        uncertainty=_uncertainty(),
        validation=_validation(),
        admission_state=EvidenceAdmissionState.ADMITTED,
    )

    replay = create_evidence_domain_admission_record(
        domain_id="radar-uncertainty",
        domain_version="v1",
        domain_type="RADAR_UNCERTAINTY",
        sources=(_source(),),
        transformations=(_transformation(),),
        uncertainty=_uncertainty(),
        validation=_validation(),
        admission_state=EvidenceAdmissionState.ADMITTED,
    )

    assert record == replay
    assert len(record.record_hash) == 64
    assert record.l3_effect == "NONE_UNTIL_GOVERNED_INTEGRATION"
    assert record.exclusions == EXCLUSIONS


def test_payload_preserves_provenance_and_uncertainty() -> None:
    record = create_evidence_domain_admission_record(
        domain_id="debris-drift",
        domain_version="v1",
        domain_type="DEBRIS_DRIFT",
        sources=(_source(),),
        transformations=(_transformation(),),
        uncertainty=_uncertainty(),
        validation=_validation(),
        admission_state=EvidenceAdmissionState.PROPOSED,
    )

    payload = record.to_payload()

    assert payload["sources"][0]["citation"]
    assert payload["transformations"][0]["sequence_index"] == 0
    assert payload["uncertainty"]["representation_type"] == "INTERVAL"
    assert payload["validation"]["report_id"] == "RADAR-VALIDATION-V1"


def test_rejects_admitted_record_without_validation_pass() -> None:
    with pytest.raises(ValueError, match="validation PASS"):
        create_evidence_domain_admission_record(
            domain_id="search-coverage",
            domain_version="v1",
            domain_type="SEARCH_COVERAGE",
            sources=(_source(),),
            transformations=(_transformation(),),
            uncertainty=_uncertainty(),
            validation=_validation(disposition="FAIL"),
            admission_state=EvidenceAdmissionState.ADMITTED,
        )


def test_rejects_non_contiguous_transformation_history() -> None:
    transformation = replace(_transformation(), sequence_index=1)

    with pytest.raises(ValueError, match="contiguous and ordered"):
        create_evidence_domain_admission_record(
            domain_id="prior-search-non-detection",
            domain_version="v1",
            domain_type="PRIOR_SEARCH_NON_DETECTION",
            sources=(_source(),),
            transformations=(transformation,),
            uncertainty=_uncertainty(),
            validation=_validation(),
            admission_state=EvidenceAdmissionState.PROPOSED,
        )


def test_rejects_automatic_l3_effect_or_tampered_hash() -> None:
    record = create_evidence_domain_admission_record(
        domain_id="radar-uncertainty",
        domain_version="v1",
        domain_type="RADAR_UNCERTAINTY",
        sources=(_source(),),
        transformations=(_transformation(),),
        uncertainty=_uncertainty(),
        validation=_validation(),
        admission_state=EvidenceAdmissionState.PROPOSED,
    )

    with pytest.raises(ValueError, match="automatically affect L3"):
        replace(record, l3_effect="DIRECT")

    with pytest.raises(ValueError, match="canonical payload"):
        replace(record, record_hash="d" * 64)
