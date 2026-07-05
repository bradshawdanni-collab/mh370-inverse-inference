"""Tests for deterministic posterior trajectory ranking."""

from mh370_inverse_inference.inference.posterior import PosteriorProbability
from mh370_inverse_inference.inference.ranking import rank_posteriors


def test_rank_posteriors_sorts_by_descending_probability() -> None:
    ranked = rank_posteriors(
        (
            PosteriorProbability("low", 0.1),
            PosteriorProbability("high", 0.7),
            PosteriorProbability("middle", 0.2),
        )
    )

    assert [item.trajectory_id for item in ranked] == ["high", "middle", "low"]


def test_rank_posteriors_breaks_ties_by_identifier() -> None:
    ranked = rank_posteriors(
        (
            PosteriorProbability("zeta", 0.4),
            PosteriorProbability("alpha", 0.4),
            PosteriorProbability("beta", 0.2),
        )
    )

    assert [item.trajectory_id for item in ranked] == ["alpha", "zeta", "beta"]


def test_rank_posteriors_does_not_mutate_input_order() -> None:
    original = (
        PosteriorProbability("b", 0.3),
        PosteriorProbability("a", 0.7),
    )

    ranked = rank_posteriors(original)

    assert [item.trajectory_id for item in original] == ["b", "a"]
    assert [item.trajectory_id for item in ranked] == ["a", "b"]


def test_rank_posteriors_accepts_empty_input() -> None:
    assert rank_posteriors(()) == ()
