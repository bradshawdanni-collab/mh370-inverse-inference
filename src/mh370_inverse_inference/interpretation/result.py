"""Immutable deterministic L3.2 interpretation result contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation.models import InterpretationRequest

CONTRACT_VERSION = "L3.2"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class InterpretationStatus(StrEnum):
    """Stable neutral interpretation outcomes."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class InterpretationReason(StrEnum):
    """Stable reasons for the neutral L3.2 result envelope."""

    OK = "OK"
    POLICY_REJECTED = "POLICY_REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class InterpretationResult:
    """Frozen, content-addressed neutral result for one interpretation request."""

    input_hash: str
    interpretation_contract_version: str
    interpretation_policy_version: str
    status: InterpretationStatus
    reason_codes: tuple[InterpretationReason, ...]
    derived_claims: tuple[()]
    result_hash: str

    @classmethod
    def _from_request(
        cls,
        request: InterpretationRequest,
        *,
        interpretation_policy_version: str,
        status: InterpretationStatus,
        reason_codes: tuple[InterpretationReason, ...],
    ) -> InterpretationResult:
        canonical_payload: dict[str, Any] = {
            "derived_claims": [],
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
        object.__setattr__(result, "derived_claims", ())
        object.__setattr__(result, "result_hash", sha256_payload(canonical_payload))
        result._validate()
        return result

    def _validate(self) -> None:
        _sha256(self.input_hash, "input_hash")
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
        if self.derived_claims:
            raise ValueError("derived_claims must be empty in L3.2")
        _sha256(self.result_hash, "result_hash")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which result_hash is derived."""
        return {
            "derived_claims": [],
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
) -> InterpretationResult:
    """Seal one L3.1 request into a neutral deterministic L3.2 result."""
    if type(request) is not InterpretationRequest:
        raise TypeError("request must be InterpretationRequest")
    if type(status) is not InterpretationStatus:
        raise TypeError("status must be InterpretationStatus")
    if any(type(reason) is not InterpretationReason for reason in reason_codes):
        raise TypeError("reason_codes must contain InterpretationReason values")
    return InterpretationResult._from_request(
        request,
        interpretation_policy_version=interpretation_policy_version,
        status=status,
        reason_codes=reason_codes,
    )
