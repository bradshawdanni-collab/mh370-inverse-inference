"""Immutable deterministic L4.0 constrained reasoning input contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation.result import InterpretationResult

CONTRACT_VERSION = "L4.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be blank")


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class ConstrainedReasoningRequest:
    """Content-addressed L4 input derived only from an L3 result."""

    interpretation_result_hash: str
    interpretation_input_hash: str
    interpretation_contract_version: str
    ordered_claim_hashes: tuple[str, ...]
    reasoning_policy_version: str
    reasoning_contract_version: str
    request_hash: str

    @classmethod
    def _from_interpretation_result(
        cls,
        result: InterpretationResult,
        *,
        reasoning_policy_version: str,
    ) -> ConstrainedReasoningRequest:
        canonical_payload: dict[str, Any] = {
            "interpretation_contract_version": (
                result.interpretation_contract_version
            ),
            "interpretation_input_hash": result.input_hash,
            "interpretation_result_hash": result.result_hash,
            "ordered_claim_hashes": [
                claim.claim_hash for claim in result.derived_claims
            ],
            "reasoning_contract_version": CONTRACT_VERSION,
            "reasoning_policy_version": reasoning_policy_version,
        }
        request = object.__new__(cls)
        object.__setattr__(
            request,
            "interpretation_result_hash",
            result.result_hash,
        )
        object.__setattr__(
            request,
            "interpretation_input_hash",
            result.input_hash,
        )
        object.__setattr__(
            request,
            "interpretation_contract_version",
            result.interpretation_contract_version,
        )
        object.__setattr__(
            request,
            "ordered_claim_hashes",
            tuple(claim.claim_hash for claim in result.derived_claims),
        )
        object.__setattr__(
            request,
            "reasoning_policy_version",
            reasoning_policy_version,
        )
        object.__setattr__(
            request,
            "reasoning_contract_version",
            CONTRACT_VERSION,
        )
        object.__setattr__(request, "request_hash", sha256_payload(canonical_payload))
        request._validate()
        return request

    def _validate(self) -> None:
        _sha256(self.interpretation_result_hash, "interpretation_result_hash")
        _sha256(self.interpretation_input_hash, "interpretation_input_hash")
        _non_empty(
            self.interpretation_contract_version,
            "interpretation_contract_version",
        )
        for claim_hash in self.ordered_claim_hashes:
            _sha256(claim_hash, "ordered_claim_hashes item")
        _non_empty(self.reasoning_policy_version, "reasoning_policy_version")
        if self.reasoning_contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"reasoning_contract_version must be {CONTRACT_VERSION}"
            )
        _sha256(self.request_hash, "request_hash")
        if self.request_hash != sha256_payload(self.canonical_payload()):
            raise ValueError("request_hash must match the canonical payload")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact payload from which request_hash is derived."""
        return {
            "interpretation_contract_version": self.interpretation_contract_version,
            "interpretation_input_hash": self.interpretation_input_hash,
            "interpretation_result_hash": self.interpretation_result_hash,
            "ordered_claim_hashes": list(self.ordered_claim_hashes),
            "reasoning_contract_version": self.reasoning_contract_version,
            "reasoning_policy_version": self.reasoning_policy_version,
        }

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical request payload with its content identity."""
        return {**self.canonical_payload(), "request_hash": self.request_hash}
