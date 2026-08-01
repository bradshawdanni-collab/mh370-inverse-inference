from __future__ import annotations

from dataclasses import replace

import pytest

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    CombinedAdmissibilityResult,
)
from mh370_inverse_inference.explanation.validation import (
    ORDERED_VALIDATION_CHECKS,
    validate_inverse_explanation,
)


def _result(
    *,
    disposition: str = "ADMISSIBLE",
    failed_constraints: tuple[str, ...] = (),
) -> CombinedAdmissibilityResult:
    return CombinedAdmissibilityResult(
        disposition=disposition,
        failed_constraints=failed_constraints,
        bto_validation_id="mh370-seventh-arc-l0.4-validation",
        bto_validation_version="v1",
        bto_output_artifact_id="mh370-seventh-arc-l0.4-validation-output",
        bto_output_artifact_version="v1",
        reachability_contract_version="AIRCRAFT-REACHABILITY-1",
        reachability_start_source_id="state-start",
        reachability_start_source_version="v1",
        reachability_end_source_id="state-end",
        reachability_end_source_version="v1",
        reachability_envelope_source_id="aircraft-envelope",
        reachability_envelope_source_version="v1",
        bfo_artifact_id="BFO-VALIDATION-REPORT-V1",
        bfo_artifact_version="BFO-VALIDATION-1",
        bfo_report_hash="a" * 64,
        bfo_model_version="BFO-COMPONENT-MODEL-1",
    )


def test_validates_admissible_explanation() -> None:
    report = validate_inverse_explanation(_result())

    assert report.disposition == "PASS"
    assert report.failed_checks == ()
    assert report.ordered_checks == ORDERED_VALIDATION_CHECKS
    assert report.production_explanation_hash == report.independent_explanation_hash
    assert len(report.replay_hash) == 64
    assert len(report.report_hash) == 64


def test_validates_not_admissible_explanation() -> None:
    report = validate_inverse_explanation(
        _result(
            disposition="NOT_ADMISSIBLE",
            failed_constraints=(
                "AIRCRAFT_REACHABILITY_ADMISSIBLE",
                "BFO_VALIDATION_PASS",
            ),
        )
    )

    assert report.disposition == "PASS"
    assert report.representative_outcomes == ("ADMISSIBLE", "NOT_ADMISSIBLE")


def test_validation_is_deterministic() -> None:
    first = validate_inverse_explanation(_result())
    second = validate_inverse_explanation(_result())

    assert first == second


def test_rejects_incomplete_provenance() -> None:
    result = replace(_result(), bfo_artifact_id="")

    with pytest.raises(ValueError, match="provenance must be complete"):
        validate_inverse_explanation(result)


def test_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="CombinedAdmissibilityResult"):
        validate_inverse_explanation(object())  # type: ignore[arg-type]
