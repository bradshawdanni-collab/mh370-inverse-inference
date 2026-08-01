from dataclasses import replace

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    BFOAdmissionRecord,
    evaluate_combined_admissibility,
)
from mh370_inverse_inference.aircraft.reachability_contract import ReachabilityResult
from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.provenance.satcom_linkage import (
    build_admitted_seventh_arc_l04_linkage,
)
from mh370_inverse_inference.satcom.bfo_components import BFOComponentInputs
from mh370_inverse_inference.satcom.bfo_contract import BFOObservation
from mh370_inverse_inference.satcom.bfo_validation import validate_bfo_model


def _reachability(admissible: bool = True) -> ReachabilityResult:
    return ReachabilityResult(
        admissible=admissible,
        failed_constraints=() if admissible else ("TURN_RATE_EXCEEDED",),
        elapsed_seconds=60.0,
        start_source_id="radar-start",
        start_source_version="v1",
        end_source_id="satcom-end",
        end_source_version="v1",
        envelope_source_id="b777-envelope",
        envelope_source_version="v1",
        envelope_model_version="model-1",
    )


def _bfo_admission() -> BFOAdmissionRecord:
    observation = BFOObservation(
        observation_id="bfo-1",
        timestamp_utc="2014-03-08T00:00:00Z",
        bfo_hz=5.0,
        uncertainty_hz=0.5,
        source_artifact_id="bfo-source",
        source_artifact_version="v1",
        source_citation="source:1",
        calibration_source_id="calibration",
        calibration_source_version="v1",
        admission_state=ArtifactAdmissionState.ADMITTED,
    )
    inputs = BFOComponentInputs(
        satellite_motion_hz=1.0,
        aircraft_motion_hz=2.0,
        earth_rotation_reference_frame_hz=1.0,
        fixed_calibration_hz=1.0,
        reference_frequency_hz=1_646_500_000.0,
        speed_of_light_mps=299_792_458.0,
        constants_source_id="constants",
        constants_source_version="v1",
        model_version="bfo-model-1",
        admission_state=ArtifactAdmissionState.ADMITTED,
    )
    return BFOAdmissionRecord(
        validation_report=validate_bfo_model(observation, inputs),
        admission_state=ArtifactAdmissionState.ADMITTED,
        disposition="FINAL_ADMISSION_REVIEW_PASS",
        artifact_id="BFO-VALIDATION-REPORT-V1",
        artifact_version="BFO-VALIDATION-1",
    )


def test_all_admitted_inputs_are_admissible() -> None:
    result = evaluate_combined_admissibility(
        build_admitted_seventh_arc_l04_linkage(),
        _reachability(),
        _bfo_admission(),
    )

    assert result.disposition == "ADMISSIBLE"
    assert result.failed_constraints == ()
    assert result.bto_validation_id == "mh370-seventh-arc-l0.4-validation"
    assert result.bfo_artifact_id == "BFO-VALIDATION-REPORT-V1"


def test_failures_preserve_canonical_order() -> None:
    bfo = _bfo_admission()
    failing_report = replace(bfo.validation_report, disposition="FAIL")
    result = evaluate_combined_admissibility(
        build_admitted_seventh_arc_l04_linkage(),
        _reachability(admissible=False),
        replace(
            bfo,
            validation_report=failing_report,
            admission_state=ArtifactAdmissionState.PROPOSED,
        ),
    )

    assert result.disposition == "NOT_ADMISSIBLE"
    assert result.failed_constraints == (
        "AIRCRAFT_REACHABILITY_ADMISSIBLE",
        "BFO_VALIDATION_ADMITTED",
        "BFO_VALIDATION_PASS",
    )


def test_wrong_types_fail_closed() -> None:
    try:
        evaluate_combined_admissibility(object(), _reachability(), _bfo_admission())
    except TypeError as exc:
        assert "bto_linkage" in str(exc)
    else:
        raise AssertionError("expected TypeError")
