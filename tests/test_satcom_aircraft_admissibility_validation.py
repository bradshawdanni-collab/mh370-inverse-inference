from mh370_inverse_inference.admissibility.satcom_aircraft import BFOAdmissionRecord
from mh370_inverse_inference.admissibility.satcom_aircraft_validation import (
    validate_combined_admissibility,
)
from mh370_inverse_inference.aircraft.reachability_contract import ReachabilityResult
from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.provenance.satcom_linkage import (
    build_admitted_seventh_arc_l04_linkage,
)
from mh370_inverse_inference.satcom.bfo_validation import BFOValidationReport


def _bfo_report(disposition: str = "PASS") -> BFOValidationReport:
    return BFOValidationReport(
        disposition=disposition,
        ordered_checks=("CHECK",),
        failed_checks=() if disposition == "PASS" else ("CHECK",),
        production_components=(("SATELLITE_MOTION", 1.0),),
        independent_components=(("SATELLITE_MOTION", 1.0),),
        maximum_component_difference_hz=0.0,
        production_residual_hz=0.0,
        independent_residual_hz=0.0,
        residual_difference_hz=0.0,
        provenance={"component_model_version": "BFO-COMPONENTS-1"},
        exclusions=("NO_LOCATION_CLAIM",),
        report_hash="a" * 64,
    )


def _reachability(admissible: bool = True) -> ReachabilityResult:
    return ReachabilityResult(
        admissible=admissible,
        failed_constraints=() if admissible else ("TURN_RATE_EXCEEDED",),
        elapsed_seconds=60.0,
        start_source_id="start",
        start_source_version="v1",
        end_source_id="end",
        end_source_version="v1",
        envelope_source_id="envelope",
        envelope_source_version="v1",
        envelope_model_version="model-v1",
    )


def _admission(disposition: str = "PASS") -> BFOAdmissionRecord:
    return BFOAdmissionRecord(
        validation_report=_bfo_report(disposition),
        admission_state=ArtifactAdmissionState.ADMITTED,
        disposition="FINAL_ADMISSION_REVIEW_PASS",
        artifact_id="bfo-validation",
        artifact_version="v1",
    )


def test_reproduces_admissible_outcome() -> None:
    report = validate_combined_admissibility(
        build_admitted_seventh_arc_l04_linkage(),
        _reachability(True),
        _admission("PASS"),
    )

    assert report.disposition == "PASS"
    assert report.production_disposition == "ADMISSIBLE"
    assert report.independent_disposition == "ADMISSIBLE"
    assert report.failed_checks == ()
    assert len(report.report_hash) == 64


def test_reproduces_not_admissible_outcome_and_order() -> None:
    report = validate_combined_admissibility(
        build_admitted_seventh_arc_l04_linkage(),
        _reachability(False),
        _admission("FAIL"),
    )

    assert report.disposition == "PASS"
    assert report.production_disposition == "NOT_ADMISSIBLE"
    assert report.production_failed_constraints == (
        "AIRCRAFT_REACHABILITY_ADMISSIBLE",
        "BFO_VALIDATION_PASS",
    )
    assert report.independent_failed_constraints == (
        "AIRCRAFT_REACHABILITY_ADMISSIBLE",
        "BFO_VALIDATION_PASS",
    )


def test_replay_hash_is_deterministic() -> None:
    args = (
        build_admitted_seventh_arc_l04_linkage(),
        _reachability(True),
        _admission("PASS"),
    )
    first = validate_combined_admissibility(*args)
    second = validate_combined_admissibility(*args)

    assert first.replay_hash == second.replay_hash
    assert first.report_hash == second.report_hash
    assert first.provenance == second.provenance
