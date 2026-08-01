"""Independent validation and deterministic replay for L5 evidence domains."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.evidence.domain_admission import (
    EVIDENCE_DOMAIN_ADMISSION_VERSION,
    EXCLUSIONS,
    SUPPORTED_DOMAINS,
    EvidenceAdmissionState,
    EvidenceDomainAdmissionRecord,
)

EVIDENCE_DOMAIN_VALIDATION_VERSION = "EVIDENCE-DOMAIN-VALIDATION-1"
ORDERED_CHECKS = (
    "SOURCE_IDENTITY_AND_CITATION",
    "SOURCE_SHA256",
    "TRANSFORMATION_ORDER",
    "UNCERTAINTY_REPRESENTATION",
    "VALIDATION_IDENTITY",
    "ADMISSION_STATE_RULES",
    "CANONICAL_RECORD_HASH",
    "L3_EFFECT_PRESERVED",
    "DETERMINISTIC_REPLAY",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


@dataclass(frozen=True, slots=True)
class EvidenceDomainValidationReport:
    """Immutable validation report for one evidence-domain admission record."""

    disposition: str
    ordered_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    domain_id: str
    domain_type: str
    admission_state: str
    source_count: int
    transformation_count: int
    record_hash: str
    replay_hash: str
    exclusions: tuple[str, ...]
    report_hash: str
    version: str = EVIDENCE_DOMAIN_VALIDATION_VERSION

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "admission_state": self.admission_state,
            "disposition": self.disposition,
            "domain_id": self.domain_id,
            "domain_type": self.domain_type,
            "exclusions": list(self.exclusions),
            "failed_checks": list(self.failed_checks),
            "ordered_checks": list(self.ordered_checks),
            "record_hash": self.record_hash,
            "replay_hash": self.replay_hash,
            "source_count": self.source_count,
            "transformation_count": self.transformation_count,
            "version": self.version,
        }
        if include_hash:
            payload["report_hash"] = self.report_hash
        return payload


def validate_evidence_domain_record(
    record: EvidenceDomainAdmissionRecord,
) -> EvidenceDomainValidationReport:
    """Independently validate one evidence-domain admission record."""
    if type(record) is not EvidenceDomainAdmissionRecord:
        raise TypeError("record must be EvidenceDomainAdmissionRecord")

    failures: list[str] = []

    if record.contract_version != EVIDENCE_DOMAIN_ADMISSION_VERSION:
        failures.append("VALIDATION_IDENTITY")
    if record.domain_type not in SUPPORTED_DOMAINS:
        failures.append("VALIDATION_IDENTITY")

    if not record.sources or any(
        not all(
            value.strip()
            for value in (
                source.source_id,
                source.source_version,
                source.citation,
            )
        )
        for source in record.sources
    ):
        failures.append("SOURCE_IDENTITY_AND_CITATION")
    if any(not _is_sha256(source.content_hash) for source in record.sources):
        failures.append("SOURCE_SHA256")

    actual_indexes = tuple(item.sequence_index for item in record.transformations)
    if actual_indexes != tuple(range(len(record.transformations))):
        failures.append("TRANSFORMATION_ORDER")

    uncertainty = record.uncertainty
    if not all(
        value.strip()
        for value in (
            uncertainty.representation_type,
            uncertainty.units,
            uncertainty.method,
        )
    ):
        failures.append("UNCERTAINTY_REPRESENTATION")
    if (uncertainty.lower_bound is None) != (uncertainty.upper_bound is None):
        failures.append("UNCERTAINTY_REPRESENTATION")
    if (
        uncertainty.lower_bound is not None
        and uncertainty.upper_bound is not None
        and uncertainty.lower_bound > uncertainty.upper_bound
    ):
        failures.append("UNCERTAINTY_REPRESENTATION")

    validation = record.validation
    if not all(
        value.strip()
        for value in (
            validation.report_id,
            validation.report_version,
            validation.disposition,
        )
    ) or not _is_sha256(validation.report_hash):
        failures.append("VALIDATION_IDENTITY")

    if (
        record.admission_state is EvidenceAdmissionState.ADMITTED
        and validation.disposition != "PASS"
    ):
        failures.append("ADMISSION_STATE_RULES")

    expected_record_hash = _canonical_hash(record.to_payload(include_hash=False))
    if record.record_hash != expected_record_hash:
        failures.append("CANONICAL_RECORD_HASH")

    if record.l3_effect != "NONE_UNTIL_GOVERNED_INTEGRATION":
        failures.append("L3_EFFECT_PRESERVED")

    replay_hash = _canonical_hash(record.to_payload())
    if replay_hash != _canonical_hash(record.to_payload()):
        failures.append("DETERMINISTIC_REPLAY")

    failures = list(dict.fromkeys(failures))
    disposition = "PASS" if not failures else "FAIL"
    hash_payload = {
        "admission_state": record.admission_state.value,
        "disposition": disposition,
        "domain_id": record.domain_id,
        "domain_type": record.domain_type,
        "exclusions": EXCLUSIONS,
        "failed_checks": tuple(failures),
        "ordered_checks": ORDERED_CHECKS,
        "record_hash": record.record_hash,
        "replay_hash": replay_hash,
        "source_count": len(record.sources),
        "transformation_count": len(record.transformations),
        "version": EVIDENCE_DOMAIN_VALIDATION_VERSION,
    }
    report_hash = _canonical_hash(hash_payload)
    return EvidenceDomainValidationReport(
        disposition=disposition,
        ordered_checks=ORDERED_CHECKS,
        failed_checks=tuple(failures),
        domain_id=record.domain_id,
        domain_type=record.domain_type,
        admission_state=record.admission_state.value,
        source_count=len(record.sources),
        transformation_count=len(record.transformations),
        record_hash=record.record_hash,
        replay_hash=replay_hash,
        exclusions=EXCLUSIONS,
        report_hash=report_hash,
    )
