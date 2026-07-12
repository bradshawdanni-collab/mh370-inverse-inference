"""Deterministic L3.5 executor for allowlisted neutral interpretation rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.interpretation.claim import (
    ClaimStatus,
    NeutralClaimType,
    build_neutral_derived_claim,
)
from mh370_inverse_inference.interpretation.models import InterpretationRequest
from mh370_inverse_inference.interpretation.result import (
    InterpretationReason,
    InterpretationResult,
    InterpretationStatus,
    build_interpretation_result,
)

CONTRACT_VERSION = "L3.5"
RULE_VERSION = "1.0.0"
OPERATION = "neutral_rule_execution"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class NeutralRuleId(StrEnum):
    """Allowlisted neutral rules with fixed structural semantics."""

    SOURCE_PRESENT = "SOURCE_PRESENT"
    OBSERVATION_LINKED = "OBSERVATION_LINKED"
    VALIDATION_PRESENT = "VALIDATION_PRESENT"
    EVIDENCE_CONSUMED = "EVIDENCE_CONSUMED"


@dataclass(frozen=True, slots=True)
class _RuleDefinition:
    claim_type: NeutralClaimType
    statement: str
    support_field: str


_RULES: dict[NeutralRuleId, _RuleDefinition] = {
    NeutralRuleId.SOURCE_PRESENT: _RuleDefinition(
        claim_type=NeutralClaimType.SOURCE_PRESENT,
        statement="Registered source identity is present.",
        support_field="registry_evidence_id",
    ),
    NeutralRuleId.OBSERVATION_LINKED: _RuleDefinition(
        claim_type=NeutralClaimType.OBSERVATION_LINKED,
        statement="Registered observation identity is linked.",
        support_field="registry_evidence_id",
    ),
    NeutralRuleId.VALIDATION_PRESENT: _RuleDefinition(
        claim_type=NeutralClaimType.VALIDATION_PASSED,
        statement="Registered validation identity is present.",
        support_field="validation_hash",
    ),
    NeutralRuleId.EVIDENCE_CONSUMED: _RuleDefinition(
        claim_type=NeutralClaimType.EVIDENCE_CONSUMED,
        statement="Accepted evidence projection was consumed.",
        support_field="evidence_hash",
    ),
}


def _sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True, init=False)
class NeutralRuleExecution:
    """Content-addressed record of one deterministic neutral-rule execution."""

    executor_contract_version: str
    operation: str
    rule_id: NeutralRuleId
    rule_version: str
    input_hash: str
    output_hash: str
    op_signature_hash: str
    result: InterpretationResult

    @classmethod
    def _from_result(
        cls,
        *,
        rule_id: NeutralRuleId,
        input_hash: str,
        op_signature_hash: str,
        result: InterpretationResult,
    ) -> NeutralRuleExecution:
        execution = object.__new__(cls)
        object.__setattr__(execution, "executor_contract_version", CONTRACT_VERSION)
        object.__setattr__(execution, "operation", OPERATION)
        object.__setattr__(execution, "rule_id", rule_id)
        object.__setattr__(execution, "rule_version", RULE_VERSION)
        object.__setattr__(execution, "input_hash", input_hash)
        object.__setattr__(execution, "output_hash", result.result_hash)
        object.__setattr__(execution, "op_signature_hash", op_signature_hash)
        object.__setattr__(execution, "result", result)
        execution._validate()
        return execution

    def _validate(self) -> None:
        if self.executor_contract_version != CONTRACT_VERSION:
            raise ValueError(f"executor_contract_version must be {CONTRACT_VERSION}")
        if self.operation != OPERATION:
            raise ValueError(f"operation must be {OPERATION}")
        if self.rule_version != RULE_VERSION:
            raise ValueError(f"rule_version must be {RULE_VERSION}")
        _sha256(self.input_hash, "input_hash")
        _sha256(self.output_hash, "output_hash")
        _sha256(self.op_signature_hash, "op_signature_hash")
        if self.input_hash != self.result.input_hash:
            raise ValueError("input_hash must equal result input_hash")
        if self.output_hash != self.result.result_hash:
            raise ValueError("output_hash must equal result result_hash")

    def to_payload(self) -> dict[str, Any]:
        """Return the deterministic execution record payload."""
        return {
            "executor_contract_version": self.executor_contract_version,
            "input_hash": self.input_hash,
            "op_signature_hash": self.op_signature_hash,
            "operation": self.operation,
            "output_hash": self.output_hash,
            "result": self.result.to_payload(),
            "rule_id": self.rule_id.value,
            "rule_version": self.rule_version,
        }


def execute_neutral_rule(
    request: InterpretationRequest,
    *,
    rule_id: NeutralRuleId,
    interpretation_policy_version: str,
) -> NeutralRuleExecution:
    """Apply one allowlisted neutral rule and seal its claim into a result."""
    if type(request) is not InterpretationRequest:
        raise TypeError("request must be InterpretationRequest")
    if type(rule_id) is not NeutralRuleId:
        raise TypeError("rule_id must be NeutralRuleId")
    if not interpretation_policy_version.strip():
        raise ValueError("interpretation_policy_version cannot be blank")

    definition = _RULES[rule_id]
    support_id = getattr(request, definition.support_field)
    permitted_evidence_ids = frozenset(
        (
            request.registry_evidence_id,
            request.evidence_hash,
            request.validation_hash,
        )
    )
    claim = build_neutral_derived_claim(
        claim_type=definition.claim_type,
        statement=definition.statement,
        supporting_evidence_ids=(support_id,),
        permitted_evidence_ids=permitted_evidence_ids,
        interpretation_rule_id=rule_id.value,
        interpretation_rule_version=RULE_VERSION,
        claim_status=ClaimStatus.ASSERTED,
    )
    result = build_interpretation_result(
        request,
        interpretation_policy_version=interpretation_policy_version,
        status=InterpretationStatus.ACCEPTED,
        reason_codes=(InterpretationReason.OK,),
        derived_claims=(claim,),
    )
    op_signature_hash = sha256_payload(
        {
            "executor_contract_version": CONTRACT_VERSION,
            "interpretation_policy_version": interpretation_policy_version,
            "operation": OPERATION,
            "rule_id": rule_id.value,
            "rule_version": RULE_VERSION,
        }
    )
    return NeutralRuleExecution._from_result(
        rule_id=rule_id,
        input_hash=request.input_hash,
        op_signature_hash=op_signature_hash,
        result=result,
    )
