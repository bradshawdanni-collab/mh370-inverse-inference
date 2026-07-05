"""Tests for L6 posterior normalization."""

import math

import pytest

from mh370_inverse_inference.inference.posterior import (
    HypothesisScore,
    normalize_posteriors,
)


def test_posteriors_normalize_to_one() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.5, log_likelihood=0.0),
            HypothesisScore("b", prior=0.3, log_likelihood=-1.0),
            HypothesisScore("c", prior=0.2, log_likelihood=-2.0),
        )
    )

    assert len(result) == 3
    assert sum(item.probability for item in result) == pytest.approx(1.0)
    assert all(math.isfinite(item.probability) for item in result)
    assert all(item.probability >= 0.0 for item in result)


def test_equal_priors_and_likelihoods_produce_equal_posteriors() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.5, log_likelihood=-3.0),
            HypothesisScore("b", prior=0.5, log_likelihood=-3.0),
        )
    )

    assert result[0].probability == pytest.approx(0.5)
    assert result[1].probability == pytest.approx(0.5)


def test_higher_prior_weighted_log_score_has_more_posterior_mass() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.8, log_likelihood=-1.0),
            HypothesisScore("b", prior=0.2, log_likelihood=-1.0),
        )
    )

    assert result[0].probability > result[1].probability


def test_normalization_is_shift_invariant() -> None:
    base = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.5, log_likelihood=-1.0),
            HypothesisScore("b", prior=0.5, log_likelihood=-2.0),
        )
    )
    shifted = normalize_posteriors(
        (
            HypothesisScore("a", prior=0.5, log_likelihood=-1001.0),
            HypothesisScore("b", prior=0.5, log_likelihood=-1002.0),
        )
    )

    assert shifted[0].probability == pytest.approx(base[0].probability)
    assert shifted[1].probability == pytest.approx(base[1].probability)


def test_zero_prior_remains_zero() -> None:
    result = normalize_posteriors(
        (
            HypothesisScore("a", prior=1.0, log_likelihood=-1000.0),
            HypothesisScore("b", prior=0.0, log_likelihood=1000.0),
        )
    )

    assert result[0].probability == pytest.approx(1.0)
    assert result[1].probability == 0.0


def test_invalid_hypothesis_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        HypothesisScore("a", prior=-0.1, log_likelihood=0.0)

    with pytest.raises(ValueError, match="finite"):
        HypothesisScore("a", prior=0.5, log_likelihood=math.inf)


def test_empty_duplicate_and_all_zero_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="at least one"):
        normalize_posteriors(())

    with pytest.raises(ValueError, match="unique"):
        normalize_posteriors(
            (
                HypothesisScore("a", prior=0.5, log_likelihood=0.0),
                HypothesisScore("a", prior=0.5, log_likelihood=0.0),
            )
        )

    with pytest.raises(ValueError, match="positive"):
        normalize_posteriors(
            (
                HypothesisScore("a", prior=0.0, log_likelihood=0.0),
                HypothesisScore("b", prior=0.0, log_likelihood=0.0),
            )
        )
