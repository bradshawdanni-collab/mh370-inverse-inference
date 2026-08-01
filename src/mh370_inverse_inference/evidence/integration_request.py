"""Immutable deterministic ED1.2 evidence-domain integration request."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.domain_admission import (
    EVIDENCE_DOMAIN_ADMISSION_VERSION,
    EXCLUSIONS as ADMISSION_EXCLUSIONS,
    SUPPORTED_DOMAINS,
    EvidenceAdmissionState,
    EvidenceDomainAdmissionRecord,
)
from mh370_inverse_inference.evidence.domain_validation import (
    EVIDENCE_DOMAIN_VALIDATION_VERSION,
    EvidenceDomainValidationReport,
)

CONTRACT_NAMESPACE = "ED1.2"
CONTRACT_VERSION = "EVIDENCE-DOMAIN-INTEGRATION-REQUEST-1"
L3_EFFECT = "NONE_UNTIL_GOVERNED_INTEGRATION"
SCOPE_EXCLUSIONS = (
    "NO_EVIDENCE_FUSION",
    "NO_SCORING",
    "NO_WEIGHTING",
    "NO_HYPOTHESIS_RANKING",
    "NO_TRAJECTORY_RANKING",
    "NO_L3_MODIFICATION",
    "NO_ENDPOINT_SELECTION",
    "NO_SEARCH_AREA_RECOMMENDATION",
    "NO_LOCATION_CLAIM",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class EvidenceDomainIntegrationRequest:
    """Content-addressed request over exact ordered ED1.0 and ED1.1 lineage."""

    ordered_domain_ids: tuple[str, ...]
    ordered_domain_versions: tuple[str, ...]
    ordered_domain_types: tuple[str, ...]
    ordered_record_hashes: tuple[str, ...]
    ordered_validation_report_hashes: tuple[str, ...]
    ordered_validation_replay_hashes: tuple[str, ...]
    integration_policy_id: str
    integration_policy_version: str
    admission_contract_version: str
    validation_contract_version: str
    integration_request_contract_version: str
    contract_namespace: str
    l3_effect: str
    scope_exclusions: tuple[str, ...]
    request_hash: str

    @classmethod
    def _from_lineage(
        cls,
        records: tuple[EvidenceDomainAdmissionRecord, ...],
        reports: tuple[EvidenceDomainValidationReport, ...],
        *,
        integration_policy_id: str,
        integration_policy_version: str,
    ) -> EvidenceDomainIntegrationRequest:
        canonical_payload: dict[str, Any] = {
            "admission_contract_version": EVIDENCE_DOMAIN_ADMISSION_VERSION,
            "contract_namespace": CONTRACT_NAMESPACE,
            "integration_policy_id": integration_policy_id,
            "integration_policy_version": integration_policy_version,
            "integration_request_contract_version": CONTRACT_VERSION,
            "l3_effect": L3_EFFECT,
            "ordered_domain_ids": [record.domain_id for record in records],
            "ordered_domain_types": [record.domain_type for record in records],
            "ordered_domain_versions": [record.domain_version for record in records],
            "ordered_record_hashes": [record.record_hash for record in records],
            "ordered_validation_replay_hashes": [
                report.replay_hash for report in reports
            ],
            "ordered_validation_report_hashes": [
                report.report_hash for report in reports
            ],
            "scope_exclusions": list(SCOPE_EXCLUSIONS),
            "validation_contract_version": EVIDENCE_DOMAIN_VALIDATION_VERSION,
        }
        request = object.__new__(cls)
        object.__setattr__(
            request,
            "ordered_domain_ids",
            tuple(record.domain_id for record in records),
        )
        object.__setattr__(
            request,
            "ordered_domain_versions",
            tuple(record.domain_version for record in records),
        )
        object.__setattr__(
            request,
            "ordered_domain_types",
            tuple(record.domain_type for record in records),
        )
        object.__setattr__(
            request,
            "ordered_record_hashes",
            tuple(record.record_hash for record in records),
        )
        object.__setattr__(
            request,
            "ordered_validation_report_hashes",
            tuple(report.report_hash for report in reports),
        )
        object.__setattr__(
            request,
            "ordered_validation_replay_hashes",
            tuple(report.replay_hash for report in reports),
        )
        object.__setattr__(request, "integration_policy_id", integration_policy_id)
        object.__setattr__(
            request,
            "integration_policy_version",
            integration_policy_version,
        )
        object.__setattr__(
            request,
            "admission_contract_version",
            EVIDENCE_DOMAIN_ADMISSION_VERSION,
        )
        object.__setattr__(
            request,
            "validation_contract_version",
            EVIDENCE_DOMAIN_VALIDATION_VERSION,
        )
        object.__setattr__(
            request,
            "integration_request_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(request, "contract_namespace", CONTRACT_NAMESPACE)
        object.__setattr__(request, "l3_effect", L3_EFFECT)
        object.__setattr__(request, "scope_exclusions", SCOPE_EXCLUSIONS)
        object.__setattr__(request, "request_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        field_lengths = {
            len(self.ordered_domain_ids),
            len(self.ordered_domain_versions),
            len(self.ordered_domain_types),
            len(self.ordered_record_hashes),
            len(self.ordered_validation_report_hashes),
            len(self.ordered_validation_replay_hashes),
        }
        if field_lengths != {len(self.ordered_record_hashes)}:
            raise ValueError("ordered integration lineage lengths must match")
        if len(self.ordered_record_hashes) < 2:
            raise ValueError("at least two admitted evidence records are required")
        for domain_id in self.ordered_domain_ids:
            _non_empty(domain_id, "ordered_domain_ids item")
        for domain_version in self.ordered_domain_versions:
            _non_empty(domain_version, "ordered_domain_versions item")
        if any(
            domain_type not in SUPPORTED_DOMAINS
            for domain_type in self.ordered_domain_types
        ):
            raise ValueError("ordered_domain_types contains an unsupported domain")
        for record_hash in self.ordered_record_hashes:
            _sha256(record_hash, "ordered_record_hashes item")
        for report_hash in self.ordered_validation_report_hashes:
            _sha256(report_hash, "ordered_validation_report_hashes item")
        for replay_hash in self.ordered_validation_replay_hashes:
            _sha256(replay_hash, "ordered_validation_replay_hashes item")
        if len(set(self.ordered_record_hashes)) != len(self.ordered_record_hashes):
            raise ValueError("ordered_record_hashes cannot contain duplicates")
        if len(set(self.ordered_validation_report_hashes)) != len(
            self.ordered_validation_report_hashes
        ):
            raise ValueError(
                "ordered_validation_report_hashes cannot contain duplicates"
            )
        _non_empty(self.integration_policy_id, "integration_policy_id")
        _non_empty(self.integration_policy_version, "integration_policy_version")
        if self.admission_contract_version != EVIDENCE_DOMAIN_ADMISSION_VERSION:
            raise ValueError("admission_contract_version is invalid")
        if self.validation_contract_version != EVIDENCE_DOMAIN_VALIDATION_VERSION:
            raise ValueError("validation_contract_version is invalid")
        if self.integration_request_contract_version != CONTRACT_VERSION:
            raise ValueError("integration_request_contract_version is invalid")
        if self.contract_namespace != CONTRACT_NAMESPACE:
            raise ValueError("contract_namespace is invalid")
        if self.l3_effect != L3_EFFECT:
            raise ValueError("l3_effect must preserve the ED1 boundary")
        if self.scope_exclusions != SCOPE_EXCLUSIONS:
            raise ValueError("scope_exclusions must preserve the ED1.2 boundary")
        _sha256(self.request_hash, "request_hash")
        if self.request_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("request_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which request_hash is derived."""
        return {
            "admission_contract_version": self.admission_contract_version,
            "contract_namespace": self.contract_namespace,
            "integration_policy_id": self.integration_policy_id,
            "integration_policy_version": self.integration_policy_version,
            "integration_request_contract_version": (
                self.integration_request_contract_version
            ),
            "l3_effect": self.l3_effect,
            "ordered_domain_ids": list(self.ordered_domain_ids),
            "ordered_domain_types": list(self.ordered_domain_types),
            "ordered_domain_versions": list(self.ordered_domain_versions),
            "ordered_record_hashes": list(self.ordered_record_hashes),
            "ordered_validation_replay_hashes": list(
                self.ordered_validation_replay_hashes
            ),
            "ordered_validation_report_hashes": list(
                self.ordered_validation_report_hashes
            ),
            "scope_exclusions": list(self.scope_exclusions),
            "validation_contract_version": self.validation_contract_version,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "request_hash": self.request_hash}


def build_evidence_domain_integration_request(
    records: tuple[EvidenceDomainAdmissionRecord, ...],
    reports: tuple[EvidenceDomainValidationReport, ...],
    *,
    integration_policy_id: str,
    integration_policy_version: str,
) -> EvidenceDomainIntegrationRequest:
    """Bind exact admitted ED1.0 and passing ED1.1 lineage into one request."""
    if type(records) is not tuple:
        raise TypeError("records must be a tuple")
    if type(reports) is not tuple:
        raise TypeError("reports must be a tuple")
    if any(type(record) is not EvidenceDomainAdmissionRecord for record in records):
        raise TypeError("records must contain EvidenceDomainAdmissionRecord values")
    if any(type(report) is not EvidenceDomainValidationReport for report in reports):
        raise TypeError("reports must contain EvidenceDomainValidationReport values")
    if len(records) < 2:
        raise ValueError("at least two admitted evidence records are required")
    if len(records) != len(reports):
        raise ValueError("each evidence record must have one validation report")

    for record, report in zip(records, reports, strict=True):
        if record.admission_state is not EvidenceAdmissionState.ADMITTED:
            raise ValueError("all evidence records must be ADMITTED")
        if record.contract_version != EVIDENCE_DOMAIN_ADMISSION_VERSION:
            raise ValueError("record admission contract version is invalid")
        if record.domain_type not in SUPPORTED_DOMAINS:
            raise ValueError("record contains an unsupported evidence domain")
        if record.l3_effect != L3_EFFECT:
            raise ValueError("record l3_effect must preserve the ED1 boundary")
        if record.exclusions != ADMISSION_EXCLUSIONS:
            raise ValueError("record exclusions must preserve the ED1.0 boundary")
        if report.disposition != "PASS" or report.failed_checks:
            raise ValueError("all evidence validation reports must PASS")
        if report.version != EVIDENCE_DOMAIN_VALIDATION_VERSION:
            raise ValueError("validation report contract version is invalid")
        if report.record_hash != record.record_hash:
            raise ValueError("validation report must reference its paired record")
        if report.domain_id != record.domain_id:
            raise ValueError("validation report domain_id must match its record")
        if report.domain_type != record.domain_type:
            raise ValueError("validation report domain_type must match its record")
        if report.admission_state != EvidenceAdmissionState.ADMITTED.value:
            raise ValueError("validation report must preserve ADMITTED state")
        if report.exclusions != ADMISSION_EXCLUSIONS:
            raise ValueError("validation report exclusions must preserve ED1.1")

    record_hashes = tuple(record.record_hash for record in records)
    report_hashes = tuple(report.report_hash for report in reports)
    replay_hashes = tuple(report.replay_hash for report in reports)
    domain_identities = tuple(
        (record.domain_id, record.domain_version) for record in records
    )
    if len(set(record_hashes)) != len(record_hashes):
        raise ValueError("records cannot contain duplicate record hashes")
    if len(set(report_hashes)) != len(report_hashes):
        raise ValueError("reports cannot contain duplicate report hashes")
    if len(set(replay_hashes)) != len(replay_hashes):
        raise ValueError("reports cannot contain duplicate replay hashes")
    if len(set(domain_identities)) != len(domain_identities):
        raise ValueError("records cannot contain duplicate domain identities")
    _non_empty(integration_policy_id, "integration_policy_id")
    _non_empty(integration_policy_version, "integration_policy_version")
    return EvidenceDomainIntegrationRequest._from_lineage(
        records,
        reports,
        integration_policy_id=integration_policy_id,
        integration_policy_version=integration_policy_version,
    )
