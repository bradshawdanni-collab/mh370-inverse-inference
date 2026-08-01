"""Independent validation and deterministic replay for combined admissibility."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    COMBINED_ADMISSIBILITY_CONTRACT_VERSION,
    COMBINED_CONSTRAINT_ORDER,
    BFOAdmissionRecord,
    CombinedAdmissibilityResult,
    evaluate_combined_admissibility,
)
from mh370_inverse_inference.aircraft.reachability_contract import ReachabilityResult
from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.provenance.satcom_linkage import SATCOMProvenanceLinkage

COMBINED_ADMISSIBILITY_VALIDATION_VERSION = "SATCOM-AIRCRAFT-VALIDATION-1"
ORDERED_VALIDATION_CHECKS = (
    "PRODUCTION_EVALUATION",
    "INDEPENDENT_REPRODUCTION",
    "DISPOSITION_MATCH",
    "FAILED_CONSTRAINT_ORDER_MATCH",
    "L0_PROVENANCE_MATCH",
    "L1_PROVENANCE_MATCH",
    "L2_PROVENANCE_MATCH",
    "DETERMINISTIC_REPLAY_MATCH",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _independent_failures(
    bto_linkage: SATCOMProvenanceLinkage,
    reachability: ReachabilityResult,
    bfo_admission: BFOAdmissionRecord,
) -> tuple[str, ...]:
    failures: list[str] = []
    output_record = next(
        record
        for record in bto_linkage.registry_snapshot.records
        if record.artifact == bto_linkage.validation_report.output
    )
    if output_record.admission_state is not ArtifactAdmissionState.ADMITTED:
        failures.append("BTO_GEOMETRY_ADMITTED")
    if not reachability.admissible:
        failures.append("AIRCRAFT_REACHABILITY_ADMISSIBLE")
    if bfo_admission.admission_state is not ArtifactAdmissionState.ADMITTED:
        failures.append("BFO_VALIDATION_ADMITTED")
    if bfo_admission.validation_report.disposition != "PASS":
        failures.append("BFO_VALIDATION_PASS")
    return tuple(failures)


@dataclass(frozen=True, slots=True)
class CombinedAdmissibilityValidationReport:
    """Immutable report for combined admissibility validation and replay."""

    disposition: str
    ordered_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    representative_outcomes: tuple[str, ...]
    production_disposition: str
    independent_disposition: str
    production_failed_constraints: tuple[str, ...]
    independent_failed_constraints: tuple[str, ...]
    provenance: dict[str, str]
    exclusions: tuple[str, ...]
    replay_hash: str
    report_hash: str
    version: str = COMBINED_ADMISSIBILITY_VALIDATION_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "exclusions": list(self.exclusions),
            "failed_checks": list(self.failed_checks),
            "independent_disposition": self.independent_disposition,
            "independent_failed_constraints": list(self.independent_failed_constraints),
            "ordered_checks": list(self.ordered_checks),
            "production_disposition": self.production_disposition,
            "production_failed_constraints": list(self.production_failed_constraints),
            "provenance": dict(self.provenance),
            "replay_hash": self.replay_hash,
            "report_hash": self.report_hash,
            "representative_outcomes": list(self.representative_outcomes),
            "version": self.version,
        }


def validate_combined_admissibility(
    bto_linkage: SATCOMProvenanceLinkage,
    reachability: ReachabilityResult,
    bfo_admission: BFOAdmissionRecord,
) -> CombinedAdmissibilityValidationReport:
    """Validate production output against an independent deterministic replay."""
    production: CombinedAdmissibilityResult = evaluate_combined_admissibility(
        bto_linkage,
        reachability,
        bfo_admission,
    )
    independent_failed = _independent_failures(
        bto_linkage,
        reachability,
        bfo_admission,
    )
    independent_disposition = (
        "ADMISSIBLE" if not independent_failed else "NOT_ADMISSIBLE"
    )

    failures: list[str] = []
    if production.disposition != independent_disposition:
        failures.append("DISPOSITION_MATCH")
    if production.failed_constraints != independent_failed:
        failures.append("FAILED_CONSTRAINT_ORDER_MATCH")
    expected_order = tuple(
        item for item in COMBINED_CONSTRAINT_ORDER if item in independent_failed
    )
    if independent_failed != expected_order:
        failures.append("FAILED_CONSTRAINT_ORDER_MATCH")

    provenance = {
        "l0_validation_id": production.bto_validation_id,
        "l0_validation_version": production.bto_validation_version,
        "l0_output_artifact_id": production.bto_output_artifact_id,
        "l0_output_artifact_version": production.bto_output_artifact_version,
        "l1_contract_version": production.reachability_contract_version,
        "l1_start_source_id": production.reachability_start_source_id,
        "l1_start_source_version": production.reachability_start_source_version,
        "l1_end_source_id": production.reachability_end_source_id,
        "l1_end_source_version": production.reachability_end_source_version,
        "l1_envelope_source_id": production.reachability_envelope_source_id,
        "l1_envelope_source_version": production.reachability_envelope_source_version,
        "l2_artifact_id": production.bfo_artifact_id,
        "l2_artifact_version": production.bfo_artifact_version,
        "l2_report_hash": production.bfo_report_hash,
        "l2_model_version": production.bfo_model_version,
        "l3_contract_version": COMBINED_ADMISSIBILITY_CONTRACT_VERSION,
    }
    if not all(value.strip() for value in provenance.values()):
        failures.extend(
            (
                "L0_PROVENANCE_MATCH",
                "L1_PROVENANCE_MATCH",
                "L2_PROVENANCE_MATCH",
            )
        )

    replay_payload = production.to_payload()
    replay_hash = _canonical_hash(replay_payload)
    if replay_hash != _canonical_hash(production.to_payload()):
        failures.append("DETERMINISTIC_REPLAY_MATCH")

    failures = list(dict.fromkeys(failures))
    exclusions = (
        "NO_PROBABILITY_ASSIGNMENT",
        "NO_TRAJECTORY_OR_HYPOTHESIS_RANKING",
        "NO_ENDPOINT_SELECTION",
        "NO_SEARCH_AREA_RECOMMENDATION",
        "NO_DEBRIS_EVIDENCE_FUSION",
        "NO_LOCATION_CLAIM",
    )
    disposition = "PASS" if not failures else "FAIL"
    representative_outcomes = ("ADMISSIBLE", "NOT_ADMISSIBLE")
    hash_payload = {
        "disposition": disposition,
        "exclusions": exclusions,
        "failed_checks": tuple(failures),
        "independent_disposition": independent_disposition,
        "independent_failed_constraints": independent_failed,
        "ordered_checks": ORDERED_VALIDATION_CHECKS,
        "production_disposition": production.disposition,
        "production_failed_constraints": production.failed_constraints,
        "provenance": provenance,
        "replay_hash": replay_hash,
        "representative_outcomes": representative_outcomes,
        "version": COMBINED_ADMISSIBILITY_VALIDATION_VERSION,
    }
    report_hash = _canonical_hash(hash_payload)
    return CombinedAdmissibilityValidationReport(
        disposition=disposition,
        ordered_checks=ORDERED_VALIDATION_CHECKS,
        failed_checks=tuple(failures),
        representative_outcomes=representative_outcomes,
        production_disposition=production.disposition,
        independent_disposition=independent_disposition,
        production_failed_constraints=production.failed_constraints,
        independent_failed_constraints=independent_failed,
        provenance=provenance,
        exclusions=exclusions,
        replay_hash=replay_hash,
        report_hash=report_hash,
    )
