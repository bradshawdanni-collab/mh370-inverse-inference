"""Common admission boundary for additional MH370 evidence domains."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

EVIDENCE_DOMAIN_ADMISSION_VERSION = "EVIDENCE-DOMAIN-ADMISSION-1"
SUPPORTED_DOMAINS = (
    "RADAR_UNCERTAINTY",
    "DEBRIS_DRIFT",
    "PRIOR_SEARCH_NON_DETECTION",
    "SEARCH_COVERAGE",
)
EXCLUSIONS = (
    "NO_EVIDENCE_FUSION",
    "NO_HYPOTHESIS_RANKING",
    "NO_ENDPOINT_SELECTION",
    "NO_SEARCH_AREA_RECOMMENDATION",
    "NO_LOCATION_CLAIM",
    "NO_AUTOMATIC_L3_EFFECT",
)


class EvidenceAdmissionState(StrEnum):
    """Governed lifecycle states for an evidence-domain record."""

    PROPOSED = "PROPOSED"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    """Immutable source and citation identity."""

    source_id: str
    source_version: str
    citation: str
    content_hash: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.source_id,
                self.source_version,
                self.citation,
                self.content_hash,
            )
        ):
            raise ValueError("source identity and citation must be complete")
        if len(self.content_hash) != 64:
            raise ValueError("content_hash must be SHA-256 hex")

    def to_payload(self) -> dict[str, str]:
        return {
            "citation": self.citation,
            "content_hash": self.content_hash,
            "source_id": self.source_id,
            "source_version": self.source_version,
        }


@dataclass(frozen=True, slots=True)
class TransformationStep:
    """One ordered transformation applied to source evidence."""

    sequence_index: int
    operation: str
    implementation_version: str
    parameters_hash: str

    def __post_init__(self) -> None:
        if self.sequence_index < 0:
            raise ValueError("sequence_index must be non-negative")
        if not self.operation.strip() or not self.implementation_version.strip():
            raise ValueError("transformation identity must be complete")
        if len(self.parameters_hash) != 64:
            raise ValueError("parameters_hash must be SHA-256 hex")

    def to_payload(self) -> dict[str, Any]:
        return {
            "implementation_version": self.implementation_version,
            "operation": self.operation,
            "parameters_hash": self.parameters_hash,
            "sequence_index": self.sequence_index,
        }


@dataclass(frozen=True, slots=True)
class UncertaintyRepresentation:
    """Explicit uncertainty representation for one evidence domain."""

    representation_type: str
    units: str
    lower_bound: float | None
    upper_bound: float | None
    method: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.representation_type,
                self.units,
                self.method,
            )
        ):
            raise ValueError("uncertainty representation must be complete")
        if (self.lower_bound is None) != (self.upper_bound is None):
            raise ValueError("uncertainty bounds must be provided together")
        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.lower_bound > self.upper_bound
        ):
            raise ValueError("uncertainty lower_bound exceeds upper_bound")

    def to_payload(self) -> dict[str, Any]:
        return {
            "lower_bound": self.lower_bound,
            "method": self.method,
            "representation_type": self.representation_type,
            "units": self.units,
            "upper_bound": self.upper_bound,
        }


@dataclass(frozen=True, slots=True)
class ValidationIdentity:
    """Identity of the validation report governing admission."""

    report_id: str
    report_version: str
    report_hash: str
    disposition: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.report_id,
                self.report_version,
                self.report_hash,
                self.disposition,
            )
        ):
            raise ValueError("validation identity must be complete")
        if len(self.report_hash) != 64:
            raise ValueError("report_hash must be SHA-256 hex")

    def to_payload(self) -> dict[str, str]:
        return {
            "disposition": self.disposition,
            "report_hash": self.report_hash,
            "report_id": self.report_id,
            "report_version": self.report_version,
        }


@dataclass(frozen=True, slots=True)
class EvidenceDomainAdmissionRecord:
    """Immutable admission record for one additional evidence domain."""

    domain_id: str
    domain_version: str
    domain_type: str
    sources: tuple[EvidenceSource, ...]
    transformations: tuple[TransformationStep, ...]
    uncertainty: UncertaintyRepresentation
    validation: ValidationIdentity
    admission_state: EvidenceAdmissionState
    l3_effect: str
    exclusions: tuple[str, ...]
    record_hash: str
    contract_version: str = EVIDENCE_DOMAIN_ADMISSION_VERSION

    def __post_init__(self) -> None:
        if not self.domain_id.strip() or not self.domain_version.strip():
            raise ValueError("evidence-domain identity must be complete")
        if self.domain_type not in SUPPORTED_DOMAINS:
            raise ValueError("unsupported evidence domain")
        if not self.sources:
            raise ValueError("at least one evidence source is required")
        expected_indexes = tuple(range(len(self.transformations)))
        actual_indexes = tuple(item.sequence_index for item in self.transformations)
        if actual_indexes != expected_indexes:
            raise ValueError("transformation history must be contiguous and ordered")
        if self.admission_state is EvidenceAdmissionState.ADMITTED:
            if self.validation.disposition != "PASS":
                raise ValueError("ADMITTED evidence requires validation PASS")
        if self.l3_effect != "NONE_UNTIL_GOVERNED_INTEGRATION":
            raise ValueError("evidence domain cannot automatically affect L3")
        if self.exclusions != EXCLUSIONS:
            raise ValueError("exclusions must preserve the scope boundary")
        if self.contract_version != EVIDENCE_DOMAIN_ADMISSION_VERSION:
            raise ValueError("unsupported evidence-domain contract version")
        if len(self.record_hash) != 64:
            raise ValueError("record_hash must be SHA-256 hex")
        if self.record_hash != _canonical_hash(self.to_payload(include_hash=False)):
            raise ValueError("record_hash does not match canonical payload")

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "admission_state": self.admission_state.value,
            "contract_version": self.contract_version,
            "domain_id": self.domain_id,
            "domain_type": self.domain_type,
            "domain_version": self.domain_version,
            "exclusions": list(self.exclusions),
            "l3_effect": self.l3_effect,
            "sources": [item.to_payload() for item in self.sources],
            "transformations": [item.to_payload() for item in self.transformations],
            "uncertainty": self.uncertainty.to_payload(),
            "validation": self.validation.to_payload(),
        }
        if include_hash:
            payload["record_hash"] = self.record_hash
        return payload


def create_evidence_domain_admission_record(
    *,
    domain_id: str,
    domain_version: str,
    domain_type: str,
    sources: tuple[EvidenceSource, ...],
    transformations: tuple[TransformationStep, ...],
    uncertainty: UncertaintyRepresentation,
    validation: ValidationIdentity,
    admission_state: EvidenceAdmissionState,
) -> EvidenceDomainAdmissionRecord:
    """Create a deterministic evidence-domain admission record."""
    payload = {
        "admission_state": admission_state.value,
        "contract_version": EVIDENCE_DOMAIN_ADMISSION_VERSION,
        "domain_id": domain_id,
        "domain_type": domain_type,
        "domain_version": domain_version,
        "exclusions": list(EXCLUSIONS),
        "l3_effect": "NONE_UNTIL_GOVERNED_INTEGRATION",
        "sources": [item.to_payload() for item in sources],
        "transformations": [item.to_payload() for item in transformations],
        "uncertainty": uncertainty.to_payload(),
        "validation": validation.to_payload(),
    }
    return EvidenceDomainAdmissionRecord(
        domain_id=domain_id,
        domain_version=domain_version,
        domain_type=domain_type,
        sources=sources,
        transformations=transformations,
        uncertainty=uncertainty,
        validation=validation,
        admission_state=admission_state,
        l3_effect="NONE_UNTIL_GOVERNED_INTEGRATION",
        exclusions=EXCLUSIONS,
        record_hash=_canonical_hash(payload),
    )
