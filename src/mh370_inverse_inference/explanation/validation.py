"""Independent validation and deterministic replay for inverse explanations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    COMBINED_CONSTRAINT_ORDER,
    CombinedAdmissibilityResult,
)
from mh370_inverse_inference.explanation.inverse import (
    COUNTERFACTUAL_ACTIONS,
    EXCLUSIONS,
    INVERSE_EXPLANATION_CONTRACT_VERSION,
    InverseExplanation,
    explain_combined_admissibility,
)

INVERSE_EXPLANATION_VALIDATION_VERSION = "INVERSE-EXPLANATION-VALIDATION-1"
ORDERED_VALIDATION_CHECKS = (
    "PRODUCTION_EXPLANATION",
    "INDEPENDENT_CONSTRAINT_ORDER",
    "INDEPENDENT_FAILED_CONSTRAINT_ORDER",
    "INDEPENDENT_COUNTERFACTUAL_MAPPING",
    "PROVENANCE_COMPLETENESS",
    "EXPLANATION_HASH_MATCH",
    "DETERMINISTIC_REPLAY_MATCH",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _independent_explanation_payload(
    result: CombinedAdmissibilityResult,
) -> dict[str, Any]:
    failed_constraints = tuple(
        item for item in COMBINED_CONSTRAINT_ORDER if item in result.failed_constraints
    )
    counterfactual_changes = tuple(
        (item, COUNTERFACTUAL_ACTIONS[item]) for item in failed_constraints
    )
    assumptions = (
        "L0_BTO_GEOMETRY_IS_ADMITTED_AND_IDENTITY_BOUND",
        "L1_REACHABILITY_USES_THE_RECORDED_ADMITTED_ENVELOPE",
        "L2_BFO_VALIDATION_IS_ADMITTED_AND_REPLAYABLE",
        "L3_FAILED_CONSTRAINT_ORDER_IS_CANONICAL",
    )
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
    return {
        "assumptions": assumptions,
        "contract_version": INVERSE_EXPLANATION_CONTRACT_VERSION,
        "counterfactual_changes": counterfactual_changes,
        "disposition": result.disposition,
        "evaluated_constraints": COMBINED_CONSTRAINT_ORDER,
        "exclusions": EXCLUSIONS,
        "failed_constraints": failed_constraints,
        "provenance": provenance,
    }


@dataclass(frozen=True, slots=True)
class InverseExplanationValidationReport:
    """Immutable validation report for one inverse explanation replay."""

    disposition: str
    ordered_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    representative_outcomes: tuple[str, ...]
    production_explanation_hash: str
    independent_explanation_hash: str
    replay_hash: str
    provenance: dict[str, str]
    exclusions: tuple[str, ...]
    report_hash: str
    version: str = INVERSE_EXPLANATION_VALIDATION_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "exclusions": list(self.exclusions),
            "failed_checks": list(self.failed_checks),
            "independent_explanation_hash": self.independent_explanation_hash,
            "ordered_checks": list(self.ordered_checks),
            "production_explanation_hash": self.production_explanation_hash,
            "provenance": dict(self.provenance),
            "replay_hash": self.replay_hash,
            "report_hash": self.report_hash,
            "representative_outcomes": list(self.representative_outcomes),
            "version": self.version,
        }


def validate_inverse_explanation(
    result: CombinedAdmissibilityResult,
) -> InverseExplanationValidationReport:
    """Validate one production inverse explanation against independent replay."""
    if type(result) is not CombinedAdmissibilityResult:
        raise TypeError("result must be CombinedAdmissibilityResult")

    production: InverseExplanation = explain_combined_admissibility(result)
    independent_payload = _independent_explanation_payload(result)
    independent_hash = _canonical_hash(independent_payload)

    failures: list[str] = []
    if production.evaluated_constraints != COMBINED_CONSTRAINT_ORDER:
        failures.append("INDEPENDENT_CONSTRAINT_ORDER")
    expected_failed = independent_payload["failed_constraints"]
    if production.failed_constraints != expected_failed:
        failures.append("INDEPENDENT_FAILED_CONSTRAINT_ORDER")
    expected_changes = tuple(
        (item.failed_constraint, item.required_change)
        for item in production.counterfactual_changes
    )
    if expected_changes != independent_payload["counterfactual_changes"]:
        failures.append("INDEPENDENT_COUNTERFACTUAL_MAPPING")
    if not all(value.strip() for value in production.provenance.values()):
        failures.append("PROVENANCE_COMPLETENESS")
    if production.explanation_hash != independent_hash:
        failures.append("EXPLANATION_HASH_MATCH")

    replay_hash = _canonical_hash(production.to_payload())
    if replay_hash != _canonical_hash(production.to_payload()):
        failures.append("DETERMINISTIC_REPLAY_MATCH")

    failures = list(dict.fromkeys(failures))
    disposition = "PASS" if not failures else "FAIL"
    representative_outcomes = ("ADMISSIBLE", "NOT_ADMISSIBLE")
    report_payload = {
        "disposition": disposition,
        "exclusions": EXCLUSIONS,
        "failed_checks": tuple(failures),
        "independent_explanation_hash": independent_hash,
        "ordered_checks": ORDERED_VALIDATION_CHECKS,
        "production_explanation_hash": production.explanation_hash,
        "provenance": production.provenance,
        "replay_hash": replay_hash,
        "representative_outcomes": representative_outcomes,
        "version": INVERSE_EXPLANATION_VALIDATION_VERSION,
    }
    return InverseExplanationValidationReport(
        disposition=disposition,
        ordered_checks=ORDERED_VALIDATION_CHECKS,
        failed_checks=tuple(failures),
        representative_outcomes=representative_outcomes,
        production_explanation_hash=production.explanation_hash,
        independent_explanation_hash=independent_hash,
        replay_hash=replay_hash,
        provenance=dict(production.provenance),
        exclusions=EXCLUSIONS,
        report_hash=_canonical_hash(report_payload),
    )
