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
from mh370_inverse_inference.evidence.domain_validation import (
    ORDERED_CHECKS,
    validate_evidence_domain_record,
)


def _record(domain_type: str):
    return create_evidence_domain_admission_record(
        domain_id=f"domain-{domain_type.lower()}",
        domain_version="v1",
        domain_type=domain_type,
        sources=(
            EvidenceSource(
                source_id="source-1",
                source_version="v1",
                citation="Published source citation",
                content_hash="a" * 64,
            ),
        ),
        transformations=(
            TransformationStep(
                sequence_index=0,
                operation="NORMALIZE",
                implementation_version="v1",
                parameters_hash="b" * 64,
            ),
        ),
        uncertainty=UncertaintyRepresentation(
            representation_type="INTERVAL",
            units="km",
            lower_bound=0.0,
            upper_bound=10.0,
            method="SOURCE_BOUNDED_INTERVAL",
        ),
        validation=ValidationIdentity(
            report_id="validation-1",
            report_version="v1",
            report_hash="c" * 64,
            disposition="PASS",
        ),
        admission_state=EvidenceAdmissionState.ADMITTED,
    )


@pytest.mark.parametrize(
    "domain_type",
    (
        "RADAR_UNCERTAINTY",
        "DEBRIS_DRIFT",
        "PRIOR_SEARCH_NON_DETECTION",
        "SEARCH_COVERAGE",
    ),
)
def test_validates_representative_domains(domain_type: str) -> None:
    report = validate_evidence_domain_record(_record(domain_type))

    assert report.disposition == "PASS"
    assert report.failed_checks == ()
    assert report.ordered_checks == ORDERED_CHECKS
    assert report.exclusions == EXCLUSIONS
    assert len(report.report_hash) == 64
    assert report == validate_evidence_domain_record(_record(domain_type))


def test_preserves_none_until_governed_integration() -> None:
    record = _record("RADAR_UNCERTAINTY")
    report = validate_evidence_domain_record(record)

    assert record.l3_effect == "NONE_UNTIL_GOVERNED_INTEGRATION"
    assert report.disposition == "PASS"


def test_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="EvidenceDomainAdmissionRecord"):
        validate_evidence_domain_record(object())  # type: ignore[arg-type]


def test_detects_tampered_record_hash() -> None:
    record = _record("DEBRIS_DRIFT")
    tampered = replace(record, record_hash="0" * 64)

    report = validate_evidence_domain_record(tampered)

    assert report.disposition == "FAIL"
    assert "CANONICAL_RECORD_HASH" in report.failed_checks


def test_replay_hash_is_deterministic() -> None:
    record = _record("SEARCH_COVERAGE")

    first = validate_evidence_domain_record(record)
    second = validate_evidence_domain_record(record)

    assert first.replay_hash == second.replay_hash
    assert first.report_hash == second.report_hash
