"""Deterministic ranking of posterior trajectory probabilities."""

from __future__ import annotations

from mh370_inverse_inference.inference.posterior import PosteriorProbability


def rank_posteriors(
    posteriors: tuple[PosteriorProbability, ...],
) -> tuple[PosteriorProbability, ...]:
    """Sort by descending probability and trajectory ID for deterministic ties."""
    return tuple(
        sorted(
            posteriors,
            key=lambda item: (-item.probability, item.trajectory_id),
        )
    )
