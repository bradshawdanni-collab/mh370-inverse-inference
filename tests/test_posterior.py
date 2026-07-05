"""Tests for L6 posterior normalization."""

import pytest

from mh370_inverse_inference.inference.posterior import (
    HypothesisScore,
    normalize_posteriors,
)


def test_posteriors_normalize_to_one() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.5, log_likelihood=-1.0),
            HypothesisScore("b", prior=0.5, log_likelihood=-2.0),
        )
    )

    assert sum(item.probability for item in result) == pytest.approx(1.0)
    assert result[0].probability > result[1].probability


def test_equal_evidence_preserves_prior_odds() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.75, log_likelihood=-3.0),
            HypothesisScore("b", prior=0.25, log_likelihood=-3.0),
        )
    )

    assert result[0].probability == pytest.approx(0.75)
    assert result[1].probability == pytest.approx(0.25)


def test_zero_prior_remains_zero() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=1.0, log_likelihood=-1000.0),
            HypothesisScore("b", prior=0.0, log_likelihood=1000.0),
        )
    )

    assert result[1].probability == 0.0
