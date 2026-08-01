"""Deterministic BFO component model for governed observations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.satcom.bfo_contract import (
    BFO_CONTRACT_VERSION,
    BFOObservation,
)

BFO_COMPONENT_MODEL_VERSION = "BFO-COMPONENTS-1"
BFO_COMPONENT_ORDER = (
    "SATELLITE_MOTION",
    "AIRCRAFT_MOTION",
    "EARTH_ROTATION_REFERENCE_FRAME",
    "FIXED_CALIBRATION",
)


def _finite(value: float, field: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{field} must be numeric")
    converted = float(value)
    if not isfinite(converted):
        raise ValueError(f"{field} must be finite")
    return converted


def _non_empty(value: str, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value


@dataclass(frozen=True, slots=True)
class BFOComponentInputs:
    """Explicit deterministic inputs for one BFO component evaluation."""

    satellite_motion_hz: float
    aircraft_motion_hz: float
    earth_rotation_reference_frame_hz: float
    fixed_calibration_hz: float
    reference_frequency_hz: float
    speed_of_light_mps: float
    constants_source_id: str
    constants_source_version: str
    model_version: str
    admission_state: ArtifactAdmissionState
    contract_version: str = BFO_COMPONENT_MODEL_VERSION

    def __post_init__(self) -> None:
        for field in (
            "satellite_motion_hz",
            "aircraft_motion_hz",
            "earth_rotation_reference_frame_hz",
            "fixed_calibration_hz",
            "reference_frequency_hz",
            "speed_of_light_mps",
        ):
            value = _finite(getattr(self, field), field)
            object.__setattr__(self, field, value)
        if self.reference_frequency_hz <= 0.0:
            raise ValueError("reference_frequency_hz must be positive")
        if self.speed_of_light_mps <= 0.0:
            raise ValueError("speed_of_light_mps must be positive")
        _non_empty(self.constants_source_id, "constants_source_id")
        _non_empty(self.constants_source_version, "constants_source_version")
        _non_empty(self.model_version, "model_version")
        if type(self.admission_state) is not ArtifactAdmissionState:
            raise TypeError("admission_state must be ArtifactAdmissionState")
        if self.contract_version != BFO_COMPONENT_MODEL_VERSION:
            raise ValueError("unsupported BFO component model contract version")


@dataclass(frozen=True, slots=True)
class BFOComponentResult:
    """Ordered deterministic BFO component breakdown and residual."""

    component_order: tuple[str, ...]
    components_hz: tuple[tuple[str, float], ...]
    predicted_bfo_hz: float
    observed_bfo_hz: float
    residual_hz: float
    within_uncertainty: bool
    observation_source_id: str
    observation_source_version: str
    calibration_source_id: str
    calibration_source_version: str
    constants_source_id: str
    constants_source_version: str
    model_version: str
    contract_version: str = BFO_COMPONENT_MODEL_VERSION

    def __post_init__(self) -> None:
        if self.component_order != BFO_COMPONENT_ORDER:
            raise ValueError("component_order must match BFO_COMPONENT_ORDER")
        if tuple(name for name, _ in self.components_hz) != BFO_COMPONENT_ORDER:
            raise ValueError("components_hz must preserve canonical component order")
        if type(self.within_uncertainty) is not bool:
            raise TypeError("within_uncertainty must be bool")
        for field in ("predicted_bfo_hz", "observed_bfo_hz", "residual_hz"):
            _finite(getattr(self, field), field)
        for field in (
            "observation_source_id",
            "observation_source_version",
            "calibration_source_id",
            "calibration_source_version",
            "constants_source_id",
            "constants_source_version",
            "model_version",
        ):
            _non_empty(getattr(self, field), field)
        if self.contract_version != BFO_COMPONENT_MODEL_VERSION:
            raise ValueError("unsupported BFO component model contract version")

    def to_payload(self) -> dict[str, Any]:
        return {
            "calibration_source_id": self.calibration_source_id,
            "calibration_source_version": self.calibration_source_version,
            "component_order": list(self.component_order),
            "components_hz": [
                {"component": name, "value_hz": value}
                for name, value in self.components_hz
            ],
            "constants_source_id": self.constants_source_id,
            "constants_source_version": self.constants_source_version,
            "contract_version": self.contract_version,
            "model_version": self.model_version,
            "observation_source_id": self.observation_source_id,
            "observation_source_version": self.observation_source_version,
            "observed_bfo_hz": self.observed_bfo_hz,
            "predicted_bfo_hz": self.predicted_bfo_hz,
            "residual_hz": self.residual_hz,
            "within_uncertainty": self.within_uncertainty,
        }


def evaluate_bfo_components(
    observation: BFOObservation,
    inputs: BFOComponentInputs,
) -> BFOComponentResult:
    """Evaluate an admitted BFO observation against explicit component inputs."""
    if type(observation) is not BFOObservation:
        raise TypeError("observation must be BFOObservation")
    if type(inputs) is not BFOComponentInputs:
        raise TypeError("inputs must be BFOComponentInputs")
    if observation.contract_version != BFO_CONTRACT_VERSION:
        raise ValueError("unsupported BFO observation contract version")
    if observation.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("BFO observation must be ADMITTED")
    if inputs.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("BFO component inputs must be ADMITTED")
    if (
        observation.calibration_source_id != observation.calibration_source_id.strip()
        or observation.calibration_source_version
        != observation.calibration_source_version.strip()
    ):
        raise ValueError("calibration provenance must be canonical")

    components = (
        ("SATELLITE_MOTION", inputs.satellite_motion_hz),
        ("AIRCRAFT_MOTION", inputs.aircraft_motion_hz),
        (
            "EARTH_ROTATION_REFERENCE_FRAME",
            inputs.earth_rotation_reference_frame_hz,
        ),
        ("FIXED_CALIBRATION", inputs.fixed_calibration_hz),
    )
    predicted = sum(value for _, value in components)
    residual = observation.bfo_hz - predicted

    return BFOComponentResult(
        component_order=BFO_COMPONENT_ORDER,
        components_hz=components,
        predicted_bfo_hz=predicted,
        observed_bfo_hz=observation.bfo_hz,
        residual_hz=residual,
        within_uncertainty=abs(residual) <= observation.uncertainty_hz,
        observation_source_id=observation.source_artifact_id,
        observation_source_version=observation.source_artifact_version,
        calibration_source_id=observation.calibration_source_id,
        calibration_source_version=observation.calibration_source_version,
        constants_source_id=inputs.constants_source_id,
        constants_source_version=inputs.constants_source_version,
        model_version=inputs.model_version,
    )
