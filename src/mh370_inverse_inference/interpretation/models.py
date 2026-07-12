"""Immutable contracts for deterministic L3.1 interpretation input."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.consumption.models import AcceptedEvidenceProjection
from mh370_inverse_inference.engine.hashing import sha256_payload

CONTRACT_VERSION = "L3.1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class InterpretationRequest:
    """Frozen, content-addressed input accepted by later interpretation layers."""

    registry_evidence_id: str
    evidence_id: str
    observation_id: str
    source_id: str
    evidence_hash: str
    validation_hash: str
    consumption_contract_version: str
    interpretation_contract_version: str
    input_hash: str

    @classmethod
    def _from_accepted_projection(
        cls,
        projection: AcceptedEvidenceProjection,
    ) -> InterpretationRequest:
        canonical_payload = {
            "consumption_contract_version": projection.consumption_contract_version,
            "evidence_hash": projection.evidence_hash,
            "evidence_id": projection.evidence_id,
            "interpretation_contract_version": CONTRACT_VERSION,
            "observation_id": projection.observation_id,
            "registry_evidence_id": projection.registry_evidence_id,
            "source_id": projection.source_id,
            "validation_hash": projection.validation_hash,
        }
        request = object.__new__(cls)
        for field_name, value in canonical_payload.items():
            object.__setattr__(request, field_name, value)
        object.__setattr__(request, "input_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        _sha256(self.registry_evidence_id, "registry_evidence_id")
        _non_empty(self.evidence_id, "evidence_id")
        _non_empty(self.observation_id, "observation_id")
        _non_empty(self.source_id, "source_id")
        _sha256(self.evidence_hash, "evidence_hash")
        _sha256(self.validation_hash, "validation_hash")
        _non_empty(
            self.consumption_contract_version,
            "consumption_contract_version",
        )
        if self.interpretation_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"interpretation_contract_version must be {CONTRACT_VERSION}"
            )
        _sha256(self.input_hash, "input_hash")

    def canonical_payload(self) -> dict[str, str]:
        """Return the exact payload from which the stable input hash is derived."""
        return {
            "consumption_contract_version": self.consumption_contract_version,
            "evidence_hash": self.evidence_hash,
            "evidence_id": self.evidence_id,
            "interpretation_contract_version": self.interpretation_contract_version,
            "observation_id": self.observation_id,
            "registry_evidence_id": self.registry_evidence_id,
            "source_id": self.source_id,
            "validation_hash": self.validation_hash,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "input_hash": self.input_hash}
