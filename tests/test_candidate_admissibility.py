"""Tests for deterministic candidate admissibility records."""

import math

import pytest

from mh370_inverse_inference.search.admissibility import (
    CandidateResiduals,
    ConstraintTolerance,
    evaluate_candidate_admissibility,
    evaluate_candidate_batch,
)


def test_candidate_inside_all_enabled_tolerances_is_admissible() -> None:
    decision = evaluate_candidate_admissibility(
        CandidateResiduals(
            candidate_id="candidate-a",
            bto_slant_range_m=5.0,
            bfo_hz=-1.0,
            reachability_m=50.0,
        ),
        ConstraintTolerance(
            bto_slant_range_m=10.0,
            bfo_hz=2.0,
            reachability_m=100.0,
        ),
    )

    assert decision.admissible
    assert decision.bto.passed
    assert decision.bfo.passed
    assert decision.reachability.passed


def test_candidate_outside_any_enabled_tolerance_is_rejected() -> None:
    decision = evaluate_candidate_admissibility(
        CandidateResiduals(
            candidate_id="candidate-b",
            bto_slant_range_m=11.0,
            bfo_hz=0.5,
        ),
        ConstraintTolerance(
            bto_slant_range_m=10.0,
            bfo_hz=1.0,
        ),
    )

    assert not decision.admissible
    assert not decision.bto.passed
    assert decision.bfo.passed


def test_disabled_constraint_is_explicitly_not_evaluated() -> None:
    decision = evaluate_candidate_admissibility(
        CandidateResiduals(
            candidate_id="candidate-c",
            bto_slant_range_m=0.0,
            bfo_hz=1000.0,
        ),
        ConstraintTolerance(bto_slant_range_m=1.0),
    )

    assert decision.admissible
    assert decision.bto.enabled
    assert decision.bto.passed
    assert not decision.bfo.enabled
    assert not decision.bfo.passed
    assert decision.bfo.residual == 1000.0


def test_enabled_constraint_missing_residual_is_rejected() -> None:
    decision = evaluate_candidate_admissibility(
        CandidateResiduals(candidate_id="candidate-d"),
        ConstraintTolerance(bto_slant_range_m=1.0),
    )

    assert not decision.admissible
    assert decision.bto.enabled
    assert not decision.bto.passed
    assert decision.bto.residual is None


def test_non_finite_residual_fails_closed() -> None:
    with pytest.raises(ValueError, match="finite"):
        CandidateResiduals(candidate_id="candidate-e", bfo_hz=math.inf)


def test_negative_tolerance_fails_closed() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ConstraintTolerance(bto_slant_range_m=-1.0)


def test_batch_evaluation_preserves_order() -> None:
    decisions = evaluate_candidate_batch(
        (
            CandidateResiduals(candidate_id="first", bto_slant_range_m=0.0),
            CandidateResiduals(candidate_id="second", bto_slant_range_m=2.0),
        ),
        ConstraintTolerance(bto_slant_range_m=1.0),
    )

    assert [decision.candidate_id for decision in decisions] == ["first", "second"]
    assert decisions[0].admissible
    assert not decisions[1].admissible
