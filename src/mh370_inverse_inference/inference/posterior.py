"""Posterior normalization for trajectory hypotheses."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log


@dataclass(frozen=True, slots=True)
class HypothesisScore:
    """Prior and log-likelihood for one trajectory hypothesis."""

    trajectory_id: str
    prior: float
    log_likelihood: float

    def __post_init__(self) -> None:
        if not self.trajectory_id:
            raise ValueError("trajectory_id must be non-empty")
        if not isfinite(self.prior) or self.prior < 0.0:
            raise ValueError("prior must be finite and non-negative")
        if not isfinite(self.log_likelihood):
            raise ValueError("log_likelihood must be finite")


@dataclass(frozen=True, slots=True)
class PosteriorProbability:
    """Normalized posterior probability for one trajectory."""

    trajectory_id: str
    probability: float

    def __post_init__(self) -> None:
        if not self.trajectory_id:
            raise ValueError("trajectory_id must be non-empty")
        if not isfinite(self.probability) or not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be finite and within [0, 1]")


def normalize_posteriors(
    scores: tuple[HypothesisScore, ...],
) -> tuple[PosteriorProbability, ...]:
    """Normalize priors and likelihoods using a stable log-sum-exp calculation."""
    if not scores:
        raise ValueError("at least one hypothesis score is required")
    trajectory_ids = tuple(score.trajectory_id for score in scores)
    if len(set(trajectory_ids)) != len(trajectory_ids):
        raise ValueError("trajectory_id values must be unique")
    if not any(score.prior > 0.0 for score in scores):
        raise ValueError("at least one prior must be positive")

    log_weights = tuple(
        float("-inf")
        if score.prior == 0.0
        else log(score.prior) + score.log_likelihood
        for score in scores
    )
    maximum = max(log_weights)
    normalizer = sum(exp(value - maximum) for value in log_weights)
    log_normalizer = maximum + log(normalizer)
    return tuple(
        PosteriorProbability(
            trajectory_id=score.trajectory_id,
            probability=(
                0.0
                if log_weight == float("-inf")
                else exp(log_weight - log_normalizer)
            ),
        )
        for score, log_weight in zip(scores, log_weights, strict=True)
    )
