"""Deterministic inverse explanation and counterfactual contract for L3 outcomes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    COMBINED_ADMISSIBILITY_CONTRACT_VERSION,
    COMBINED_CONSTRAINT_ORDER,
    CombinedAdmissibilityResult,
)

INVERSE_EXPLANATION_CONTRACT_VERSION = "INVERSE-EXPLANATION-1"
COUNTERFACTUAL_ACTIONS = {
    "BTO_GEOMETRY_ADMITTED": "ADMIT_BTO_GEOMETRY",
    "AIRCRAFT_REACHABILITY_ADMISSIBLE": "SATISFY_REACHABILITY",
    "BFO_VALIDATION_ADMITTED": "ADMIT_BFO_VALIDATION",
    "BFO_VALIDATION_PASS": "PASS_BFO_VALIDATION",
}
EXCLUSIONS = (
    "NO_PROBABILITY_ASSIGNMENT",
    "NO_TRAJECTORY_OR_HYPOTHESIS_RANKING",
    "NO_ENDPOINT_SELECTION",
    "NO_SEARCH_AREA_RECOMMENDATION",
    "NO_DEBRIS_EVIDENCE_FUSION",
    "NO_LOCATION_CLAIM",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class CounterfactualChange:
    """One minimal governed change required to reverse an L3 disposition."""

    failed_constraint: str
    required_change: str

    def __post_init__(self) -> None:
        if self.failed_constraint not in COMBINED_CONSTRAINT_ORDER:
            raise ValueError("unsupported failed_constraint")
        expected = COUNTERFACTUAL_ACTIONS[self.failed_constraint]
        if self.required_change != expected:
            raise ValueError("required_change does not match failed_constraint")

    def to_payload(self) -> dict[str, str]:
        return {
            "failed_constraint": self.failed_constraint,
            "required_change": self.required_change,
        }


@dataclass(frozen=True, slots=True)
class InverseExplanation:
    """Immutable explanation of an admitted L3 disposition."""

    disposition: str
    evaluated_constraints: tuple[str, ...]
    failed_constraints: tuple[str, ...]
    assumptions: tuple[str, ...]
    counterfactual_changes: tuple[CounterfactualChange, ...]
    provenance: dict[str, str]
    exclusions: tuple[str, ...]
    explanation_hash: str
    contract_version: str = INVERSE_EXPLANATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.disposition not in {"ADMISSIBLE", "NOT_ADMISSIBLE"}:
            raise ValueError("unsupported disposition")
        if self.evaluated_constraints != COMBINED_CONSTRAINT_ORDER:
            raise ValueError("evaluated_constraints must preserve canonical order")
        expected_failed = tuple(
            item for item in COMBINED_CONSTRAINT_ORDER if item in self.failed_constraints
        )
        if self.failed_constraints != expected_failed:
            raise ValueError("failed_constraints must preserve canonical order")
        if self.disposition == "ADMISSIBLE" and self.failed_constraints:
            raise ValueError("ADMISSIBLE explanations cannot contain failures")
        if self.disposition == "NOT_ADMISSIBLE" and not self.failed_constraints:
            raise ValueError("NOT_ADMISSIBLE explanations require failures")
        expected_changes = tuple(
            CounterfactualChange(item, COUNTERFACTUAL_ACTIONS[item])
            for item in self.failed_constraints
        )
        if self.counterfactual_changes != expected_changes:
            raise ValueError("counterfactual_changes must be minimal and ordered")
        if self.exclusions != EXCLUSIONS:
            raise ValueError("exclusions must preserve the contract scope boundary")
        if self.contract_version != INVERSE_EXPLANATION_CONTRACT_VERSION:
            raise ValueError("unsupported inverse explanation contract version")
        if len(self.explanation_hash) != 64:
            raise ValueError("explanation_hash must be SHA-256 hex")

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "assumptions": list(self.assumptions),
            "contract_version": self.contract_version,
            "counterfactual_changes": [
                item.to_payload() for item in self.counterfactual_changes
            ],
            "disposition": self.disposition,
            "evaluated_constraints": list(self.evaluated_constraints),
            "exclusions": list(self.exclusions),
            "failed_constraints": list(self.failed_constraints),
            "provenance": dict(self.provenance),
        }
        if include_hash:
            payload["explanation_hash"] = self.explanation_hash
        return payload


def explain_combined_admissibility(
    result: CombinedAdmissibilityResult,
) -> InverseExplanation:
    """Explain one L3 result without inference, ranking, or evidence fusion."""
    if type(result) is not CombinedAdmissibilityResult:
        raise TypeError("result must be CombinedAdmissibilityResult")
    if result.contract_version != COMBINED_ADMISSIBILITY_CONTRACT_VERSION:
        raise ValueError("result contract version is not supported")

    provenance = {
        "l0_validation_id": result.bto_validation_id,
        "l0_validation_version": result.bto_validation_version,
        "l0_output_artifact_id": result.bto_output_artifact_id,
        "l0_output_artifact_version": result.bto_output_artifact_version,
        "l1_contract_version": result.reachability_contract_version,
        "l1_start_source_id": result.reachability_start_source_id,
        "l1_start_source_version": result.reachability_start_source_version,
        "l1_end_source_id": result.reachability_end_source_id,
        "l1_end_source_version": result.reachability_end_source_version,
        "l1_envelope_source_id": result.reachability_envelope_source_id,
        "l1_envelope_source_version": result.reachability_envelope_source_version,
        "l2_artifact_id": result.bfo_artifact_id,
        "l2_artifact_version": result.bfo_artifact_version,
        "l2_report_hash": result.bfo_report_hash,
        "l2_model_version": result.bfo_model_version,
        "l3_contract_version": result.contract_version,
    }
    if not all(value.strip() for value in provenance.values()):
        raise ValueError("result provenance must be complete")

    assumptions = (
        "L0_BTO_GEOMETRY_IS_ADMITTED_AND_IDENTITY_BOUND",
        "L1_REACHABILITY_USES_THE_RECORDED_ADMITTED_ENVELOPE",
        "L2_BFO_VALIDATION_IS_ADMITTED_AND_REPLAYABLE",
        "L3_FAILED_CONSTRAINT_ORDER_IS_CANONICAL",
    )
    counterfactual_changes = tuple(
        CounterfactualChange(item, COUNTERFACTUAL_ACTIONS[item])
        for item in result.failed_constraints
    )
    hash_payload = {
        "assumptions": assumptions,
        "contract_version": INVERSE_EXPLANATION_CONTRACT_VERSION,
        "counterfactual_changes": tuple(
            (item.failed_constraint, item.required_change)
            for item in counterfactual_changes
        ),
        "disposition": result.disposition,
        "evaluated_constraints": COMBINED_CONSTRAINT_ORDER,
        "exclusions": EXCLUSIONS,
        "failed_constraints": result.failed_constraints,
        "provenance": provenance,
    }
    explanation_hash = _canonical_hash(hash_payload)
    return InverseExplanation(
        disposition=result.disposition,
        evaluated_constraints=COMBINED_CONSTRAINT_ORDER,
        failed_constraints=result.failed_constraints,
        assumptions=assumptions,
        counterfactual_changes=counterfactual_changes,
        provenance=provenance,
        exclusions=EXCLUSIONS,
        explanation_hash=explanation_hash,
    )
