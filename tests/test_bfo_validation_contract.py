"""Tests for deterministic BFO validation and independent reproduction."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.satcom.bfo_components import BFOComponentInputs
from mh370_inverse_inference.satcom.bfo_contract import BFOObservation
from mh370_inverse_inference.satcom.bfo_validation import validate_bfo_model


def _observation(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> BFOObservation:
    return BFOObservation(
        observation_id="BFO-OBS-001",
        timestamp_utc="2014-03-07T18:25:27Z",
        bfo_hz=82.0,
        uncertainty_hz=5.0,
        source_artifact_id="bfo-source",
        source_artifact_version="v1",
        source_citation="published BFO table",
        calibration_source_id="calibration-source",
        calibration_source_version="v1",
        admission_state=admission_state,
    )


def _inputs(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> BFOComponentInputs:
    return BFOComponentInputs(
        satellite_motion_hz=35.0,
        aircraft_motion_hz=40.0,
        earth_rotation_reference_frame_hz=5.0,
        fixed_calibration_hz=2.0,
        reference_frequency_hz=1_646_652_500.0,
        speed_of_light_mps=299_792_458.0,
        constants_source_id="constants-source",
        constants_source_version="v1",
        model_version="BFO-components-v1",
        admission_state=admission_state,
    )


def test_validation_passes_for_exact_independent_reproduction() -> None:
    report = validate_bfo_model(_observation(), _inputs())

    assert report.disposition == "PASS"
    assert report.failed_checks == ()
    assert report.maximum_component_difference_hz == 0.0
    assert report.production_residual_hz == 0.0
    assert report.independent_residual_hz == 0.0
    assert report.residual_difference_hz == 0.0


def test_component_order_is_preserved() -> None:
    report = validate_bfo_model(_observation(), _inputs())

    expected_names = (
        "SATELLITE_MOTION",
        "AIRCRAFT_MOTION",
        "EARTH_ROTATION_REFERENCE_FRAME",
        "FIXED_CALIBRATION",
    )
    assert tuple(name for name, _ in report.production_components) == expected_names
    assert tuple(name for name, _ in report.independent_components) == expected_names


def test_report_hash_is_deterministic() -> None:
    first = validate_bfo_model(_observation(), _inputs())
    second = validate_bfo_model(_observation(), _inputs())

    assert first.to_payload() == second.to_payload()
    assert first.report_hash == second.report_hash
    assert len(first.report_hash) == 64


def test_provenance_is_preserved() -> None:
    report = validate_bfo_model(_observation(), _inputs())

    assert report.provenance == {
        "observation_id": "BFO-OBS-001",
        "observation_source_artifact_id": "bfo-source",
        "observation_source_artifact_version": "v1",
        "calibration_source_id": "calibration-source",
        "calibration_source_version": "v1",
        "constants_source_id": "constants-source",
        "constants_source_version": "v1",
        "component_model_version": "BFO-components-v1",
    }


def test_non_admitted_observation_fails_closed() -> None:
    with pytest.raises(ValueError, match="observation must be ADMITTED"):
        validate_bfo_model(
            _observation(ArtifactAdmissionState.PROPOSED),
            _inputs(),
        )


def test_non_admitted_component_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="component inputs must be ADMITTED"):
        validate_bfo_model(
            _observation(),
            _inputs(ArtifactAdmissionState.PROPOSED),
        )


def test_type_validation_fails_closed() -> None:
    with pytest.raises(TypeError, match="observation"):
        validate_bfo_model(object(), _inputs())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="inputs"):
        validate_bfo_model(_observation(), object())  # type: ignore[arg-type]


def test_report_is_immutable() -> None:
    report = validate_bfo_model(_observation(), _inputs())

    with pytest.raises(FrozenInstanceError):
        report.disposition = "FAIL"  # type: ignore[misc]


def test_scope_exclusions_are_explicit() -> None:
    report = validate_bfo_model(_observation(), _inputs())

    assert "NO_BFO_TRAJECTORY_INVERSION" in report.exclusions
    assert "NO_ENDPOINT_INFERENCE" in report.exclusions
    assert "NO_LOCATION_CLAIM" in report.exclusions
