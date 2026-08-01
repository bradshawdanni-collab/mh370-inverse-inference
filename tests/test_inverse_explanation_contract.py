from __future__ import annotations

from dataclasses import replace

import pytest

from mh370_inverse_inference.admissibility.satcom_aircraft import (
    COMBINED_CONSTRAINT_ORDER,
    CombinedAdmissibilityResult,
)
from mh370_inverse_inference.explanation.inverse import (
    EXCLUSIONS,
    COUNTERFACTUAL_ACTIONS,
    CounterfactualChange,
    explain_combined_admissibility,
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
        bfo_artifact_version="SATCOM-AIRCRAFT-VALIDATION-1",
        bfo_report_hash="a" * 64,
        bfo_model_version="BFO-COMPONENT-MODEL-1",
    )


def test_explains_admissible_result_deterministically() -> None:
    explanation = explain_combined_admissibility(_result())

    assert explanation.disposition == "ADMISSIBLE"
    assert explanation.evaluated_constraints == COMBINED_CONSTRAINT_ORDER
    assert explanation.failed_constraints == ()
    assert explanation.counterfactual_changes == ()
    assert explanation.exclusions == EXCLUSIONS
    assert len(explanation.explanation_hash) == 64
    assert explanation == explain_combined_admissibility(_result())


def test_explains_not_admissible_with_minimal_ordered_changes() -> None:
    failed = (
        "AIRCRAFT_REACHABILITY_ADMISSIBLE",
        "BFO_VALIDATION_PASS",
    )
    explanation = explain_combined_admissibility(
        _result(disposition="NOT_ADMISSIBLE", failed_constraints=failed)
    )

    assert explanation.failed_constraints == failed
    assert explanation.counterfactual_changes == tuple(
        CounterfactualChange(item, COUNTERFACTUAL_ACTIONS[item]) for item in failed
    )


def test_payload_preserves_all_layer_identities() -> None:
    explanation = explain_combined_admissibility(_result())
    payload = explanation.to_payload()

    assert payload["provenance"]["l0_validation_id"]
    assert payload["provenance"]["l1_contract_version"]
    assert payload["provenance"]["l2_report_hash"] == "a" * 64
    assert payload["provenance"]["l3_contract_version"]


def test_rejects_incomplete_provenance() -> None:
    result = replace(_result(), bfo_artifact_id="")

    with pytest.raises(ValueError, match="provenance must be complete"):
        explain_combined_admissibility(result)


def test_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="CombinedAdmissibilityResult"):
        explain_combined_admissibility(object())  # type: ignore[arg-type]
