"""Pure deterministic evaluation engine for generated search candidates."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    """Immutable scored candidate with its original generation index."""

    candidate: tuple[tuple[str, float], ...]
    score: float
    source_index: int

    def as_dict(self) -> dict[str, float]:
        """Return a fresh dictionary representation of the candidate."""
        return dict(self.candidate)


def evaluate_candidates(
    candidates: Iterable[Mapping[str, float]],
    scorer: Callable[[Mapping[str, float]], float],
    limit: int | None = None,
) -> tuple[ScoredCandidate, ...]:
    """Score candidates and return deterministic descending results.

    Equal scores preserve original candidate-generation order.
    """
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive when provided")

    scored: list[ScoredCandidate] = []
    for source_index, candidate in enumerate(candidates):
        snapshot = dict(candidate)
        score = scorer(snapshot.copy())
        if not isfinite(score):
            raise ValueError("scorer must return a finite score")
        scored.append(
            ScoredCandidate(
                candidate=tuple(snapshot.items()),
                score=score,
                source_index=source_index,
            )
        )

    ordered = sorted(scored, key=lambda result: (-result.score, result.source_index))
    if limit is not None:
        ordered = ordered[:limit]
    return tuple(ordered)
