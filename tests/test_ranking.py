"""Tests for deterministic posterior ranking."""

from mh370_inverse_inference.inference.posterior import PosteriorProbability
from mh370_inverse_inference.inference.ranking import rank_posteriors


def test_ranking_is_descending_and_ties_use_identifier() -> None:
    ranked = rank_posteriors(
        (
            PosteriorProbability("zeta", 0.2),
            PosteriorProbability("beta", 0.4),
            PosteriorProbability("alpha", 0.4),
        )
    )

    assert [item.trajectory_id for item in ranked] == ["alpha", "beta", "zeta"]
