"""Independent deterministic validation for the governed BFO component model."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.satcom.bfo_components import (
    BFOComponentInputs,
    BFOComponentResult,
    evaluate_bfo_components,
)
from mh370_inverse_inference.satcom.bfo_contract import BFOObservation

BFO_VALIDATION_VERSION = "BFO-VALIDATION-1"
ORDERED_VALIDATION_CHECKS = (
    "OBSERVATION_ADMITTED",
    "COMPONENT_INPUTS_ADMITTED",
    "PRODUCTION_COMPONENT_MODEL",
    "INDEPENDENT_COMPONENT_REPRODUCTION",
    "COMPONENT_COMPARISON",
    "RESIDUAL_COMPARISON",
    "PROVENANCE_PRESERVATION",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _independent_components(
    inputs: BFOComponentInputs,
) -> tuple[tuple[str, float], ...]:
    return (
        ("SATELLITE_MOTION", float(inputs.satellite_motion_hz)),
        ("AIRCRAFT_MOTION", float(inputs.aircraft_motion_hz)),
        (
            "EARTH_ROTATION_REFERENCE_FRAME",
            float(inputs.earth_rotation_reference_frame_hz),
        ),
        ("FIXED_CALIBRATION", float(inputs.fixed_calibration_hz)),
    )


@dataclass(frozen=True, slots=True)
class BFOValidationReport:
    """Immutable validation and independent-reproduction report."""

    disposition: str
    ordered_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    production_components: tuple[tuple[str, float], ...]
    independent_components: tuple[tuple[str, float], ...]
    maximum_component_difference_hz: float
    production_residual_hz: float
    independent_residual_hz: float
    residual_difference_hz: float
    provenance: dict[str, str]
    exclusions: tuple[str, ...]
    report_hash: str
    version: str = BFO_VALIDATION_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "exclusions": list(self.exclusions),
            "failed_checks": list(self.failed_checks),
            "independent_components": [
                list(item) for item in self.independent_components
            ],
            "independent_residual_hz": self.independent_residual_hz,
            "maximum_component_difference_hz": self.maximum_component_difference_hz,
            "ordered_checks": list(self.ordered_checks),
            "production_components": [
                list(item) for item in self.production_components
            ],
            "production_residual_hz": self.production_residual_hz,
            "provenance": dict(self.provenance),
            "report_hash": self.report_hash,
            "residual_difference_hz": self.residual_difference_hz,
            "version": self.version,
        }


def validate_bfo_model(
    observation: BFOObservation,
    inputs: BFOComponentInputs,
) -> BFOValidationReport:
    """Compare production BFO output with an independent deterministic reproduction."""
    if type(observation) is not BFOObservation:
        raise TypeError("observation must be BFOObservation")
    if type(inputs) is not BFOComponentInputs:
        raise TypeError("inputs must be BFOComponentInputs")
    if observation.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("BFO observation must be ADMITTED")
    if inputs.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("BFO component inputs must be ADMITTED")

    production: BFOComponentResult = evaluate_bfo_components(observation, inputs)
    independent_components = _independent_components(inputs)
    independent_predicted_hz = sum(value for _, value in independent_components)
    independent_residual_hz = observation.bfo_hz - independent_predicted_hz

    production_components = tuple(production.components_hz)
    component_differences = tuple(
        abs(prod_value - independent_value)
        for (_, prod_value), (_, independent_value) in zip(
            production_components,
            independent_components,
            strict=True,
        )
    )
    maximum_component_difference_hz = max(component_differences, default=0.0)
    residual_difference_hz = abs(production.residual_hz - independent_residual_hz)

    failures: list[str] = []
    if maximum_component_difference_hz != 0.0:
        failures.append("COMPONENT_COMPARISON")
    if residual_difference_hz != 0.0:
        failures.append("RESIDUAL_COMPARISON")

    provenance = {
        "observation_id": observation.observation_id,
        "observation_source_artifact_id": observation.source_artifact_id,
        "observation_source_artifact_version": observation.source_artifact_version,
        "calibration_source_id": observation.calibration_source_id,
        "calibration_source_version": observation.calibration_source_version,
        "constants_source_id": inputs.constants_source_id,
        "constants_source_version": inputs.constants_source_version,
        "component_model_version": production.model_version,
    }
    if not all(value.strip() for value in provenance.values()):
        failures.append("PROVENANCE_PRESERVATION")

    exclusions = (
        "NO_BFO_TRAJECTORY_INVERSION",
        "NO_AIRCRAFT_VELOCITY_SELECTION",
        "NO_TRAJECTORY_RANKING",
        "NO_DEBRIS_OR_SEARCH_EVIDENCE_FUSION",
        "NO_ENDPOINT_INFERENCE",
        "NO_SEARCH_AREA_SELECTION",
        "NO_LOCATION_CLAIM",
    )
    disposition = "PASS" if not failures else "FAIL"
    hash_payload = {
        "disposition": disposition,
        "exclusions": exclusions,
        "failed_checks": tuple(failures),
        "independent_components": independent_components,
        "independent_residual_hz": independent_residual_hz,
        "maximum_component_difference_hz": maximum_component_difference_hz,
        "ordered_checks": ORDERED_VALIDATION_CHECKS,
        "production_components": production_components,
        "production_residual_hz": production.residual_hz,
        "provenance": provenance,
        "residual_difference_hz": residual_difference_hz,
        "version": BFO_VALIDATION_VERSION,
    }
    report_hash = _canonical_hash(hash_payload)
    return BFOValidationReport(
        disposition=disposition,
        ordered_checks=ORDERED_VALIDATION_CHECKS,
        failed_checks=tuple(failures),
        production_components=production_components,
        independent_components=independent_components,
        maximum_component_difference_hz=maximum_component_difference_hz,
        production_residual_hz=production.residual_hz,
        independent_residual_hz=independent_residual_hz,
        residual_difference_hz=residual_difference_hz,
        provenance=provenance,
        exclusions=exclusions,
        report_hash=report_hash,
    )
