"""Deterministic aggregation for scored search candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from mh370_inverse_inference.search.engine import ScoredCandidate


@dataclass(frozen=True, slots=True)
class SearchSummary:
    """Immutable summary of one deterministic search result set."""

    total_count: int
    selected: tuple[ScoredCandidate, ...]
    best_score: float | None
    worst_score: float | None


def aggregate_results(
    results: Iterable[ScoredCandidate],
    limit: int | None = None,
) -> SearchSummary:
    """Return a stable top-N selection and summary statistics."""
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive when provided")

    ordered = tuple(
        sorted(
            results,
            key=lambda result: (-result.score, result.source_index),
        )
    )
    selected = ordered if limit is None else ordered[:limit]

    return SearchSummary(
        total_count=len(ordered),
        selected=selected,
        best_score=None if not ordered else ordered[0].score,
        worst_score=None if not ordered else ordered[-1].score,
    )
