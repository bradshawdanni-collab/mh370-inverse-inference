"""Tests for deterministic BFO component evaluation."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.satcom.bfo_components import (
    BFO_COMPONENT_ORDER,
    BFOComponentInputs,
    evaluate_bfo_components,
)
from mh370_inverse_inference.satcom.bfo_contract import BFOObservation


def _observation(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> BFOObservation:
    return BFOObservation(
        observation_id="bfo-001",
        timestamp_utc="2014-03-07T18:25:27Z",
        bfo_hz=88.0,
        uncertainty_hz=2.0,
        frequency_unit="Hz",
        uncertainty_unit="Hz",
        source_artifact_id="atsb-bfo-table",
        source_artifact_version="v1",
        source_citation="ATSB source citation",
        calibration_source_id="calibration-series",
        calibration_source_version="v1",
        admission_state=admission_state,
    )


def _inputs(
    admission_state: ArtifactAdmissionState = ArtifactAdmissionState.ADMITTED,
) -> BFOComponentInputs:
    return BFOComponentInputs(
        satellite_motion_hz=70.0,
        aircraft_motion_hz=12.0,
        earth_rotation_reference_frame_hz=4.0,
        fixed_calibration_hz=1.0,
        reference_frequency_hz=1_646_652_500.0,
        speed_of_light_mps=299_792_458.0,
        constants_source_id="constants-register",
        constants_source_version="v1",
        model_version="BFO-components-v1",
        admission_state=admission_state,
    )


def test_component_breakdown_is_ordered_and_deterministic() -> None:
    first = evaluate_bfo_components(_observation(), _inputs())
    second = evaluate_bfo_components(_observation(), _inputs())

    assert first.component_order == BFO_COMPONENT_ORDER
    assert first.components_hz == (
        ("SATELLITE_MOTION", 70.0),
        ("AIRCRAFT_MOTION", 12.0),
        ("EARTH_ROTATION_REFERENCE_FRAME", 4.0),
        ("FIXED_CALIBRATION", 1.0),
    )
    assert first.predicted_bfo_hz == 87.0
    assert first.residual_hz == 1.0
    assert first.within_uncertainty is True
    assert first.to_payload() == second.to_payload()


def test_residual_outside_uncertainty_is_reported() -> None:
    result = evaluate_bfo_components(
        _observation(),
        BFOComponentInputs(
            satellite_motion_hz=60.0,
            aircraft_motion_hz=10.0,
            earth_rotation_reference_frame_hz=3.0,
            fixed_calibration_hz=1.0,
            reference_frequency_hz=1_646_652_500.0,
            speed_of_light_mps=299_792_458.0,
            constants_source_id="constants-register",
            constants_source_version="v1",
            model_version="BFO-components-v1",
            admission_state=ArtifactAdmissionState.ADMITTED,
        ),
    )

    assert result.predicted_bfo_hz == 74.0
    assert result.residual_hz == 14.0
    assert result.within_uncertainty is False


def test_non_admitted_observation_fails_closed() -> None:
    with pytest.raises(ValueError, match="observation must be ADMITTED"):
        evaluate_bfo_components(
            _observation(ArtifactAdmissionState.PROPOSED),
            _inputs(),
        )


def test_non_admitted_component_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="inputs must be ADMITTED"):
        evaluate_bfo_components(
            _observation(),
            _inputs(ArtifactAdmissionState.PROPOSED),
        )


def test_non_positive_declared_constants_fail_closed() -> None:
    with pytest.raises(ValueError, match="reference_frequency_hz must be positive"):
        BFOComponentInputs(
            satellite_motion_hz=1.0,
            aircraft_motion_hz=1.0,
            earth_rotation_reference_frame_hz=1.0,
            fixed_calibration_hz=1.0,
            reference_frequency_hz=0.0,
            speed_of_light_mps=299_792_458.0,
            constants_source_id="constants-register",
            constants_source_version="v1",
            model_version="BFO-components-v1",
            admission_state=ArtifactAdmissionState.ADMITTED,
        )


def test_provenance_identities_are_preserved() -> None:
    result = evaluate_bfo_components(_observation(), _inputs())

    assert result.observation_source_id == "atsb-bfo-table"
    assert result.observation_source_version == "v1"
    assert result.calibration_source_id == "calibration-series"
    assert result.calibration_source_version == "v1"
    assert result.constants_source_id == "constants-register"
    assert result.constants_source_version == "v1"
    assert result.model_version == "BFO-components-v1"


def test_result_is_immutable() -> None:
    result = evaluate_bfo_components(_observation(), _inputs())

    with pytest.raises(FrozenInstanceError):
        result.residual_hz = 0.0  # type: ignore[misc]
