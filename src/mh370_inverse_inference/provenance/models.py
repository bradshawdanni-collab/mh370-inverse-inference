"""Immutable repository-level provenance contracts for Issue #9A."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

PROVENANCE_CONTRACT_VERSION = "PROVENANCE-1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ArtifactKind(StrEnum):
    """Repository-level artifact categories."""

    SOURCE = "SOURCE"
    DERIVED = "DERIVED"
    VALIDATION = "VALIDATION"


class ArtifactAdmissionState(StrEnum):
    """Explicit lifecycle state for a provenance-governed artifact."""

    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


def _non_empty(value: str, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")
    return value


def _sha256(value: str, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _utc_z_timestamp(value: str, name: str) -> str:
    _non_empty(value, name)
    if not value.endswith("Z"):
        raise ValueError(f"{name} must use canonical UTC Z notation")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{name} must be a valid UTC timestamp") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0.0:
        raise ValueError(f"{name} must be UTC")
    return value


def _non_empty_tuple(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be tuple")
    for value in values:
        _non_empty(value, name)
    return values


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Stable identity for one exact repository artifact version."""

    artifact_id: str
    version: str
    sha256: str

    def __post_init__(self) -> None:
        _non_empty(self.artifact_id, "artifact_id")
        _non_empty(self.version, "version")
        _sha256(self.sha256, "sha256")

    def to_payload(self) -> dict[str, str]:
        """Return the canonical artifact-reference payload."""
        return {
            "artifact_id": self.artifact_id,
            "sha256": self.sha256,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Immutable bibliographic and retrieval identity for one source."""

    source_id: str
    publisher: str
    title: str
    reference_uri: str
    retrieved_at_utc: str
    licence_or_terms: str
    content_hash: str

    def __post_init__(self) -> None:
        _non_empty(self.source_id, "source_id")
        _non_empty(self.publisher, "publisher")
        _non_empty(self.title, "title")
        _non_empty(self.reference_uri, "reference_uri")
        _utc_z_timestamp(self.retrieved_at_utc, "retrieved_at_utc")
        _non_empty(self.licence_or_terms, "licence_or_terms")
        _sha256(self.content_hash, "content_hash")

    def to_payload(self) -> dict[str, str]:
        """Return the canonical source-reference payload."""
        return {
            "content_hash": self.content_hash,
            "licence_or_terms": self.licence_or_terms,
            "publisher": self.publisher,
            "reference_uri": self.reference_uri,
            "retrieved_at_utc": self.retrieved_at_utc,
            "source_id": self.source_id,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class TransformationStep:
    """One ordered deterministic transformation in an artifact history."""

    step_index: int
    operation: str
    inputs: tuple[ArtifactReference, ...]
    output: ArtifactReference
    implementation_reference: str
    configuration_id: str

    def __post_init__(self) -> None:
        if type(self.step_index) is not int:
            raise TypeError("step_index must be int")
        if self.step_index < 0:
            raise ValueError("step_index cannot be negative")
        _non_empty(self.operation, "operation")
        if type(self.inputs) is not tuple:
            raise TypeError("inputs must be tuple")
        if not self.inputs:
            raise ValueError("inputs cannot be empty")
        if any(type(item) is not ArtifactReference for item in self.inputs):
            raise TypeError("inputs must contain ArtifactReference values")
        if type(self.output) is not ArtifactReference:
            raise TypeError("output must be ArtifactReference")
        _non_empty(self.implementation_reference, "implementation_reference")
        _non_empty(self.configuration_id, "configuration_id")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical transformation-step payload."""
        return {
            "configuration_id": self.configuration_id,
            "implementation_reference": self.implementation_reference,
            "inputs": [item.to_payload() for item in self.inputs],
            "operation": self.operation,
            "output": self.output.to_payload(),
            "step_index": self.step_index,
        }


@dataclass(frozen=True, slots=True)
class ArtifactProvenanceRecord:
    """Immutable provenance record for one exact scientific artifact."""

    artifact: ArtifactReference
    kind: ArtifactKind
    admission_state: ArtifactAdmissionState
    source: SourceReference | None
    transformation_history: tuple[TransformationStep, ...]
    uncertainty_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    superseded_by: ArtifactReference | None = None
    contract_version: str = PROVENANCE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.artifact) is not ArtifactReference:
            raise TypeError("artifact must be ArtifactReference")
        if type(self.kind) is not ArtifactKind:
            raise TypeError("kind must be ArtifactKind")
        if type(self.admission_state) is not ArtifactAdmissionState:
            raise TypeError("admission_state must be ArtifactAdmissionState")
        if self.source is not None and type(self.source) is not SourceReference:
            raise TypeError("source must be SourceReference or None")
        if type(self.transformation_history) is not tuple:
            raise TypeError("transformation_history must be tuple")
        if any(
            type(step) is not TransformationStep for step in self.transformation_history
        ):
            raise TypeError(
                "transformation_history must contain TransformationStep values"
            )
        _non_empty_tuple(self.uncertainty_notes, "uncertainty_notes")
        _non_empty_tuple(self.limitations, "limitations")
        if self.contract_version != PROVENANCE_CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {PROVENANCE_CONTRACT_VERSION}")
        self._validate_source_boundary()
        self._validate_transformations()
        self._validate_supersession()

    def _validate_source_boundary(self) -> None:
        if self.kind is ArtifactKind.SOURCE:
            if self.source is None:
                raise ValueError("SOURCE artifact requires source metadata")
            if self.transformation_history:
                raise ValueError(
                    "SOURCE artifact cannot include transformation_history"
                )
            if self.artifact.sha256 != self.source.content_hash:
                raise ValueError("SOURCE artifact hash must match source content_hash")
            return
        if not self.transformation_history:
            raise ValueError(
                "DERIVED and VALIDATION artifacts require transformation_history"
            )

    def _validate_transformations(self) -> None:
        if not self.transformation_history:
            return
        indices = tuple(step.step_index for step in self.transformation_history)
        if indices != tuple(range(len(self.transformation_history))):
            raise ValueError(
                "transformation_history must use contiguous ordered step_index values"
            )
        final_output = self.transformation_history[-1].output
        if final_output != self.artifact:
            raise ValueError(
                "final transformation output must equal artifact reference"
            )

    def _validate_supersession(self) -> None:
        if self.admission_state is ArtifactAdmissionState.SUPERSEDED:
            if self.superseded_by is None:
                raise ValueError("SUPERSEDED artifact requires superseded_by")
            if self.superseded_by == self.artifact:
                raise ValueError("artifact cannot supersede itself")
            return
        if self.superseded_by is not None:
            raise ValueError(
                "superseded_by is valid only when admission_state is SUPERSEDED"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical artifact-provenance payload."""
        return {
            "admission_state": self.admission_state.value,
            "artifact": self.artifact.to_payload(),
            "contract_version": self.contract_version,
            "kind": self.kind.value,
            "limitations": list(self.limitations),
            "source": None if self.source is None else self.source.to_payload(),
            "superseded_by": (
                None if self.superseded_by is None else self.superseded_by.to_payload()
            ),
            "transformation_history": [
                step.to_payload() for step in self.transformation_history
            ],
            "uncertainty_notes": list(self.uncertainty_notes),
        }


@dataclass(frozen=True, slots=True)
class ValidationReportRecord:
    """Immutable linkage from exact input artifacts to a validation output."""

    validation_id: str
    validation_version: str
    inputs: tuple[ArtifactReference, ...]
    output: ArtifactReference
    model_version: str
    configuration_id: str
    contract_version: str = PROVENANCE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.validation_id, "validation_id")
        _non_empty(self.validation_version, "validation_version")
        if type(self.inputs) is not tuple:
            raise TypeError("inputs must be tuple")
        if not self.inputs:
            raise ValueError("inputs cannot be empty")
        if any(type(item) is not ArtifactReference for item in self.inputs):
            raise TypeError("inputs must contain ArtifactReference values")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError("inputs cannot contain duplicate artifact references")
        if type(self.output) is not ArtifactReference:
            raise TypeError("output must be ArtifactReference")
        _non_empty(self.model_version, "model_version")
        _non_empty(self.configuration_id, "configuration_id")
        if self.contract_version != PROVENANCE_CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {PROVENANCE_CONTRACT_VERSION}")

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical validation-report payload."""
        return {
            "configuration_id": self.configuration_id,
            "contract_version": self.contract_version,
            "inputs": [item.to_payload() for item in self.inputs],
            "model_version": self.model_version,
            "output": self.output.to_payload(),
            "validation_id": self.validation_id,
            "validation_version": self.validation_version,
        }
