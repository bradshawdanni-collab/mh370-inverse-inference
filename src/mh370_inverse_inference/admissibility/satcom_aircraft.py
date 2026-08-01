"""Combined deterministic BTO, BFO, and aircraft reachability admissibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.aircraft.reachability_contract import ReachabilityResult
from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.provenance.satcom_linkage import SATCOMProvenanceLinkage
from mh370_inverse_inference.satcom.bfo_validation import BFOValidationReport

COMBINED_ADMISSIBILITY_CONTRACT_VERSION = "SATCOM-AIRCRAFT-ADMISSIBILITY-1"
COMBINED_CONSTRAINT_ORDER = (
    "BTO_GEOMETRY_ADMITTED",
    "AIRCRAFT_REACHABILITY_ADMISSIBLE",
    "BFO_VALIDATION_ADMITTED",
    "BFO_VALIDATION_PASS",
)


@dataclass(frozen=True, slots=True)
class BFOAdmissionRecord:
    """Governed admission wrapper for one deterministic BFO validation report."""

    validation_report: BFOValidationReport
    admission_state: ArtifactAdmissionState
    disposition: str
    artifact_id: str
    artifact_version: str

    def __post_init__(self) -> None:
        if type(self.validation_report) is not BFOValidationReport:
            raise TypeError("validation_report must be BFOValidationReport")
        if type(self.admission_state) is not ArtifactAdmissionState:
            raise TypeError("admission_state must be ArtifactAdmissionState")
        if self.disposition != "FINAL_ADMISSION_REVIEW_PASS":
            raise ValueError("disposition must be FINAL_ADMISSION_REVIEW_PASS")
        for field in ("artifact_id", "artifact_version"):
            value = getattr(self, field)
            if type(value) is not str or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class CombinedAdmissibilityResult:
    """Deterministic combined admissibility outcome."""

    disposition: str
    failed_constraints: tuple[str, ...]
    bto_validation_id: str
    bto_validation_version: str
    bto_output_artifact_id: str
    bto_output_artifact_version: str
    reachability_contract_version: str
    reachability_start_source_id: str
    reachability_start_source_version: str
    reachability_end_source_id: str
    reachability_end_source_version: str
    reachability_envelope_source_id: str
    reachability_envelope_source_version: str
    bfo_artifact_id: str
    bfo_artifact_version: str
    bfo_report_hash: str
    bfo_model_version: str
    contract_version: str = COMBINED_ADMISSIBILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.disposition not in {"ADMISSIBLE", "NOT_ADMISSIBLE"}:
            raise ValueError("disposition must be ADMISSIBLE or NOT_ADMISSIBLE")
        if type(self.failed_constraints) is not tuple:
            raise TypeError("failed_constraints must be a tuple")
        if self.disposition == "ADMISSIBLE" and self.failed_constraints:
            raise ValueError("ADMISSIBLE results cannot contain failed constraints")
        if self.disposition == "NOT_ADMISSIBLE" and not self.failed_constraints:
            raise ValueError("NOT_ADMISSIBLE results require failed constraints")
        expected = tuple(
            item for item in COMBINED_CONSTRAINT_ORDER if item in self.failed_constraints
        )
        if self.failed_constraints != expected:
            raise ValueError("failed_constraints must preserve canonical order")
        if self.contract_version != COMBINED_ADMISSIBILITY_CONTRACT_VERSION:
            raise ValueError("unsupported combined admissibility contract version")

    def to_payload(self) -> dict[str, Any]:
        return {
            "bfo_artifact_id": self.bfo_artifact_id,
            "bfo_artifact_version": self.bfo_artifact_version,
            "bfo_model_version": self.bfo_model_version,
            "bfo_report_hash": self.bfo_report_hash,
            "bto_output_artifact_id": self.bto_output_artifact_id,
            "bto_output_artifact_version": self.bto_output_artifact_version,
            "bto_validation_id": self.bto_validation_id,
            "bto_validation_version": self.bto_validation_version,
            "contract_version": self.contract_version,
            "disposition": self.disposition,
            "failed_constraints": list(self.failed_constraints),
            "reachability_contract_version": self.reachability_contract_version,
            "reachability_end_source_id": self.reachability_end_source_id,
            "reachability_end_source_version": self.reachability_end_source_version,
            "reachability_envelope_source_id": self.reachability_envelope_source_id,
            "reachability_envelope_source_version": (
                self.reachability_envelope_source_version
            ),
            "reachability_start_source_id": self.reachability_start_source_id,
            "reachability_start_source_version": self.reachability_start_source_version,
        }


def evaluate_combined_admissibility(
    bto_linkage: SATCOMProvenanceLinkage,
    reachability: ReachabilityResult,
    bfo_admission: BFOAdmissionRecord,
) -> CombinedAdmissibilityResult:
    """Combine already-governed L0, L1, and L2 outputs without ranking."""
    if type(bto_linkage) is not SATCOMProvenanceLinkage:
        raise TypeError("bto_linkage must be SATCOMProvenanceLinkage")
    if type(reachability) is not ReachabilityResult:
        raise TypeError("reachability must be ReachabilityResult")
    if type(bfo_admission) is not BFOAdmissionRecord:
        raise TypeError("bfo_admission must be BFOAdmissionRecord")

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

    bfo_provenance = bfo_admission.validation_report.provenance
    return CombinedAdmissibilityResult(
        disposition="ADMISSIBLE" if not failures else "NOT_ADMISSIBLE",
        failed_constraints=tuple(failures),
        bto_validation_id=bto_linkage.validation_report.validation_id,
        bto_validation_version=bto_linkage.validation_report.validation_version,
        bto_output_artifact_id=bto_linkage.validation_report.output.artifact_id,
        bto_output_artifact_version=bto_linkage.validation_report.output.version,
        reachability_contract_version=reachability.contract_version,
        reachability_start_source_id=reachability.start_source_id,
        reachability_start_source_version=reachability.start_source_version,
        reachability_end_source_id=reachability.end_source_id,
        reachability_end_source_version=reachability.end_source_version,
        reachability_envelope_source_id=reachability.envelope_source_id,
        reachability_envelope_source_version=reachability.envelope_source_version,
        bfo_artifact_id=bfo_admission.artifact_id,
        bfo_artifact_version=bfo_admission.artifact_version,
        bfo_report_hash=bfo_admission.validation_report.report_hash,
        bfo_model_version=bfo_provenance["component_model_version"],
    )
