"""Immutable deterministic L4.1 constrained reasoning result contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.reasoning.models import ConstrainedReasoningRequest

CONTRACT_VERSION = "L4.1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReasoningStatus(StrEnum):
    """Stable neutral outcomes for constrained reasoning."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


class ReasoningReason(StrEnum):
    """Stable machine-readable reasons for an L4.1 result."""

    OK = "OK"
    POLICY_REJECTED = "POLICY_REJECTED"
    INSUFFICIENT_BASIS = "INSUFFICIENT_BASIS"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ConstrainedReasoningResult:
    """Content-addressed neutral result derived only from an L4.0 input."""

    request_hash: str
    reasoning_contract_version: str
    reasoning_policy_version: str
    status: ReasoningStatus
    reason_codes: tuple[ReasoningReason, ...]
    reasoning_outputs: tuple[()]
    result_hash: str

    @classmethod
    def _from_request(
        cls,
        request: ConstrainedReasoningRequest,
        *,
        status: ReasoningStatus,
        reason_codes: tuple[ReasoningReason, ...],
    ) -> ConstrainedReasoningResult:
        canonical_payload: dict[str, Any] = {
            "reason_codes": [reason.value for reason in reason_codes],
            "reasoning_contract_version": CONTRACT_VERSION,
            "reasoning_outputs": [],
            "reasoning_policy_version": request.reasoning_policy_version,
            "request_hash": request.request_hash,
            "status": status.value,
        }
        result = object.__new__(cls)
        object.__setattr__(result, "request_hash", request.request_hash)
        object.__setattr__(
            result,
            "reasoning_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(
            result,
            "reasoning_policy_version",
            request.reasoning_policy_version,
        )
        object.__setattr__(result, "status", status)
        object.__setattr__(result, "reason_codes", reason_codes)
        object.__setattr__(result, "reasoning_outputs", ())
        object.__setattr__(result, "result_hash", sha256_payload(canonical_payload))
        result._validate()
        return result

    def _validate(self) -> None:
        _sha256(self.request_hash, "request_hash")
        if self.reasoning_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"reasoning_contract_version must be {CONTRACT_VERSION}"
            )
        _non_empty(self.reasoning_policy_version, "reasoning_policy_version")
        if type(self.status) is not ReasoningStatus:
            raise TypeError("status must be ReasoningStatus")
        if not self.reason_codes:
            raise ValueError("reason_codes cannot be empty")
        if any(type(reason) is not ReasoningReason for reason in self.reason_codes):
            raise TypeError("reason_codes must contain ReasoningReason values")
        if self.reasoning_outputs:
            raise ValueError("reasoning_outputs must be empty in L4.1")
        _sha256(self.result_hash, "result_hash")
        if self.result_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("result_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which result_hash is derived."""
        return {
            "reason_codes": [reason.value for reason in self.reason_codes],
            "reasoning_contract_version": self.reasoning_contract_version,
            "reasoning_outputs": [],
            "reasoning_policy_version": self.reasoning_policy_version,
            "request_hash": self.request_hash,
            "status": self.status.value,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical result payload with its content identity."""
        return {**self.canonical_payload(), "result_hash": self.result_hash}


def build_constrained_reasoning_result(
    request: ConstrainedReasoningRequest,
    *,
    status: ReasoningStatus,
    reason_codes: tuple[ReasoningReason, ...],
) -> ConstrainedReasoningResult:
    """Seal one L4.0 input into a neutral deterministic L4.1 result."""
    if type(request) is not ConstrainedReasoningRequest:
        raise TypeError("request must be ConstrainedReasoningRequest")
    if type(status) is not ReasoningStatus:
        raise TypeError("status must be ReasoningStatus")
    if any(type(reason) is not ReasoningReason for reason in reason_codes):
        raise TypeError("reason_codes must contain ReasoningReason values")
    return ConstrainedReasoningResult._from_request(
        request,
        status=status,
        reason_codes=reason_codes,
    )
