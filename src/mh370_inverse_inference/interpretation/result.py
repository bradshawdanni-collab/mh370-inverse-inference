"""Immutable deterministic L3.4 interpretation result contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation.claim import NeutralDerivedClaim
from mh370_inverse_inference.interpretation.models import InterpretationRequest

CONTRACT_VERSION = "L3.4"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class InterpretationStatus(StrEnum):
    """Stable neutral interpretation outcomes."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class InterpretationReason(StrEnum):
    """Stable reasons for the neutral interpretation result envelope."""

    OK = "OK"
    POLICY_REJECTED = "POLICY_REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def _permitted_lineage(request: InterpretationRequest) -> frozenset[str]:
    return frozenset(
        (
            request.registry_evidence_id,
            request.evidence_hash,
            request.validation_hash,
        )
    )


@dataclass(frozen=True, slots=True, init=False)
class InterpretationResult:
    """Frozen result containing only lineage-valid neutral claims."""

    input_hash: str
    interpretation_contract_version: str
    interpretation_policy_version: str
    status: InterpretationStatus
    reason_codes: tuple[InterpretationReason, ...]
    derived_claims: tuple[NeutralDerivedClaim, ...]
    result_hash: str

    @classmethod
    def _from_request(
        cls,
        request: InterpretationRequest,
        *,
        interpretation_policy_version: str,
        status: InterpretationStatus,
        reason_codes: tuple[InterpretationReason, ...],
        derived_claims: tuple[NeutralDerivedClaim, ...],
    ) -> InterpretationResult:
        canonical_payload: dict[str, Any] = {
            "derived_claims": [claim.to_payload() for claim in derived_claims],
            "input_hash": request.input_hash,
            "interpretation_contract_version": CONTRACT_VERSION,
            "interpretation_policy_version": interpretation_policy_version,
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
        result = object.__new__(cls)
        object.__setattr__(result, "input_hash", request.input_hash)
        object.__setattr__(
            result,
            "interpretation_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(
            result,
            "interpretation_policy_version",
            interpretation_policy_version,
        )
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "reason_codes", reason_codes)
        object.__setattr__(result, "derived_claims", derived_claims)
        object.__setattr__(result, "result_hash", sha256_payload(canonical_payload))
        result._validate(request)
        return result

    def _validate(self, request: InterpretationRequest) -> None:
        _sha256(self.input_hash, "input_hash")
        if self.input_hash != request.input_hash:
            raise ValueError("input_hash must equal the request input_hash")
        if self.interpretation_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"interpretation_contract_version must be {CONTRACT_VERSION}"
            )
        _non_empty(
            self.interpretation_policy_version,
            "interpretation_policy_version",
        )
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")

        claim_hashes = [claim.claim_hash for claim in self.derived_claims]
        if len(set(claim_hashes)) != len(claim_hashes):
            raise ValueError("derived_claims cannot contain duplicate claim hashes")

        permitted_lineage = _permitted_lineage(request)
        for claim in self.derived_claims:
            if not set(claim.supporting_evidence_ids).issubset(permitted_lineage):
                raise ValueError("derived claim support is outside request lineage")

        _sha256(self.result_hash, "result_hash")
        if self.result_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("result_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which result_hash is derived."""
        return {
            "derived_claims": [claim.to_payload() for claim in self.derived_claims],
            "input_hash": self.input_hash,
            "interpretation_contract_version": self.interpretation_contract_version,
            "interpretation_policy_version": self.interpretation_policy_version,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "status": self.status.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical result payload with its content identity."""
        return {**self.canonical_payload(), "result_hash": self.result_hash}


def build_interpretation_result(
    request: InterpretationRequest,
    *,
    interpretation_policy_version: str,
    status: InterpretationStatus,
    reason_codes: tuple[InterpretationReason, ...],
    derived_claims: tuple[NeutralDerivedClaim, ...] = (),
) -> InterpretationResult:
    """Seal one request and zero or more neutral claims into an L3.4 result."""
    if type(request) is not InterpretationRequest:
        raise TypeError("request must be InterpretationRequest")
    if type(status) is not InterpretationStatus:
        raise TypeError("status must be InterpretationStatus")
    if type(reason_codes) is not tuple:
        raise TypeError("reason_codes must be tuple[InterpretationReason, ...]")
    if any(type(reason) is not InterpretationReason for reason in reason_codes):
        raise TypeError("reason_codes must contain InterpretationReason values")
    if type(derived_claims) is not tuple:
        raise TypeError("derived_claims must be tuple[NeutralDerivedClaim, ...]")
    if any(type(claim) is not NeutralDerivedClaim for claim in derived_claims):
        raise TypeError("derived_claims must contain NeutralDerivedClaim values")
    return InterpretationResult._from_request(
        request,
        interpretation_policy_version=interpretation_policy_version,
        status=status,
        reason_codes=reason_codes,
        derived_claims=derived_claims,
    )
