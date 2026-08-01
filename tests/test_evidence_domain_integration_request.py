from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from mh370_inverse_inference.evidence.domain_admission import (
    EvidenceAdmissionState,
    EvidenceDomainAdmissionRecord,
    EvidenceSource,
    TransformationStep,
    UncertaintyRepresentation,
    ValidationIdentity,
    create_evidence_domain_admission_record,
)
from mh370_inverse_inference.evidence.domain_validation import (
    validate_evidence_domain_record,
)
from mh370_inverse_inference.evidence.integration_request import (
    CONTRACT_NAMESPACE,
    CONTRACT_VERSION,
    L3_EFFECT,
    SCOPE_EXCLUSIONS,
    EvidenceDomainIntegrationRequest,
    build_evidence_domain_integration_request,
)


def _record(
    domain_type: str,
    index: int,
    *,
    admission_state: EvidenceAdmissionState = EvidenceAdmissionState.ADMITTED,
) -> EvidenceDomainAdmissionRecord:
    digest_char = "abcdef"[index]
    return create_evidence_domain_admission_record(
        domain_id=f"domain-{index}",
        domain_version="v1",
        domain_type=domain_type,
        sources=(
            EvidenceSource(
                source_id=f"source-{index}",
                source_version="v1",
                citation=f"Authoritative source {index}",
                content_hash=digest_char * 64,
            ),
        ),
        transformations=(
            TransformationStep(
                sequence_index=0,
                operation="NORMALIZE",
                implementation_version="v1",
                parameters_hash="f" * 64,
            ),
        ),
        uncertainty=UncertaintyRepresentation(
            representation_type="INTERVAL",
            units="km",
            lower_bound=0.0,
            upper_bound=float(index + 1),
            method="SOURCE_BOUNDED_INTERVAL",
        ),
        validation=ValidationIdentity(
            report_id=f"validation-{index}",
            report_version="v1",
            report_hash=digest_char * 64,
            disposition="PASS",
        ),
        admission_state=admission_state,
    )


def _request() -> EvidenceDomainIntegrationRequest:
    records = (
        _record("RADAR_UNCERTAINTY", 0),
        _record("DEBRIS_DRIFT", 1),
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)
    return build_evidence_domain_integration_request(
        records,
        reports,
        integration_policy_id="STRUCTURAL-BINDING-ONLY",
        integration_policy_version="v1",
    )


def _forge_request_hash(
    request: EvidenceDomainIntegrationRequest,
    request_hash: str,
) -> EvidenceDomainIntegrationRequest:
    forged = object.__new__(EvidenceDomainIntegrationRequest)
    for field in fields(request):
        value = (
            request_hash
            if field.name == "request_hash"
            else getattr(request, field.name)
        )
        object.__setattr__(forged, field.name, value)
    return forged


def test_builds_deterministic_content_addressed_request() -> None:
    first = _request()
    second = _request()

    assert first == second
    assert first.request_hash == second.request_hash
    assert first.to_payload()["request_hash"] == first.request_hash
    assert len(first.request_hash) == 64


def test_preserves_exact_ordered_ed1_lineage() -> None:
    request = _request()

    assert request.ordered_domain_ids == ("domain-0", "domain-1")
    assert request.ordered_domain_types == ("RADAR_UNCERTAINTY", "DEBRIS_DRIFT")
    assert request.ordered_domain_versions == ("v1", "v1")
    assert len(request.ordered_record_hashes) == 2
    assert len(request.ordered_validation_report_hashes) == 2
    assert len(request.ordered_validation_replay_hashes) == 2


def test_preserves_contract_identities_and_scope_boundary() -> None:
    request = _request()

    assert request.contract_namespace == CONTRACT_NAMESPACE == "ED1.2"
    assert request.integration_request_contract_version == CONTRACT_VERSION
    assert request.admission_contract_version == "EVIDENCE-DOMAIN-ADMISSION-1"
    assert request.validation_contract_version == "EVIDENCE-DOMAIN-VALIDATION-1"
    assert request.l3_effect == L3_EFFECT
    assert request.scope_exclusions == SCOPE_EXCLUSIONS


def test_request_is_frozen() -> None:
    request = _request()

    with pytest.raises(FrozenInstanceError):
        request.integration_policy_version = "v2"  # type: ignore[misc]


def test_requires_at_least_two_admitted_records() -> None:
    record = _record("RADAR_UNCERTAINTY", 0)
    report = validate_evidence_domain_record(record)

    with pytest.raises(ValueError, match="at least two"):
        build_evidence_domain_integration_request(
            (record,),
            (report,),
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_rejects_non_admitted_record() -> None:
    records = (
        _record(
            "RADAR_UNCERTAINTY",
            0,
            admission_state=EvidenceAdmissionState.PROPOSED,
        ),
        _record("DEBRIS_DRIFT", 1),
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)

    with pytest.raises(ValueError, match="must be ADMITTED"):
        build_evidence_domain_integration_request(
            records,
            reports,
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_rejects_failed_validation_report() -> None:
    records = (
        _record("RADAR_UNCERTAINTY", 0),
        _record("DEBRIS_DRIFT", 1),
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)
    failed = replace(reports[0], disposition="FAIL", failed_checks=("TEST",))

    with pytest.raises(ValueError, match="must PASS"):
        build_evidence_domain_integration_request(
            records,
            (failed, reports[1]),
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_rejects_mismatched_validation_lineage() -> None:
    records = (
        _record("RADAR_UNCERTAINTY", 0),
        _record("DEBRIS_DRIFT", 1),
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)

    with pytest.raises(ValueError, match="paired record"):
        build_evidence_domain_integration_request(
            records,
            (reports[1], reports[0]),
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_rejects_duplicate_records() -> None:
    record = _record("RADAR_UNCERTAINTY", 0)
    report = validate_evidence_domain_record(record)

    with pytest.raises(ValueError, match="duplicate record hashes"):
        build_evidence_domain_integration_request(
            (record, record),
            (report, report),
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_rejects_blank_policy_identity() -> None:
    records = (
        _record("RADAR_UNCERTAINTY", 0),
        _record("DEBRIS_DRIFT", 1),
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)

    with pytest.raises(ValueError, match="integration_policy_id"):
        build_evidence_domain_integration_request(
            records,
            reports,
            integration_policy_id=" ",
            integration_policy_version="v1",
        )


def test_rejects_wrong_input_types() -> None:
    with pytest.raises(TypeError, match="records must be a tuple"):
        build_evidence_domain_integration_request(
            [],  # type: ignore[arg-type]
            (),
            integration_policy_id="STRUCTURAL-BINDING-ONLY",
            integration_policy_version="v1",
        )


def test_detects_tampered_request_hash() -> None:
    request = _request()
    tampered = _forge_request_hash(request, "0" * 64)

    with pytest.raises(ValueError, match="request_hash"):
        tampered._validate()


def test_accepts_all_supported_domains_without_fusion() -> None:
    domain_types = (
        "RADAR_UNCERTAINTY",
        "DEBRIS_DRIFT",
        "PRIOR_SEARCH_NON_DETECTION",
        "SEARCH_COVERAGE",
    )
    records = tuple(
        _record(domain_type, index) for index, domain_type in enumerate(domain_types)
    )
    reports = tuple(validate_evidence_domain_record(record) for record in records)

    request = build_evidence_domain_integration_request(
        records,
        reports,
        integration_policy_id="STRUCTURAL-BINDING-ONLY",
        integration_policy_version="v1",
    )

    assert request.ordered_domain_types == domain_types
    assert "NO_EVIDENCE_FUSION" in request.scope_exclusions
    assert "NO_L3_MODIFICATION" in request.scope_exclusions
