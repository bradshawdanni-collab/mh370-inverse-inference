"""Tests for deterministic L7 result aggregation."""

import pytest

from mh370_inverse_inference.search.engine import ScoredCandidate
from mh370_inverse_inference.search.results import aggregate_results


def make_result(identifier: float, score: float, source_index: int) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=(("id", identifier),),
        score=score,
        source_index=source_index,
    )


def test_aggregate_results_orders_and_selects_top_n() -> None:
    summary = aggregate_results(
        (
            make_result(1.0, 1.0, 0),
            make_result(2.0, 3.0, 1),
            make_result(3.0, 2.0, 2),
        ),
        limit=2,
    )

    assert summary.total_count == 3
    assert [result.score for result in summary.selected] == [3.0, 2.0]
    assert summary.best_score == 3.0
    assert summary.worst_score == 1.0


def test_aggregate_results_preserves_source_order_for_ties() -> None:
    summary = aggregate_results(
        (
            make_result(3.0, 5.0, 2),
            make_result(1.0, 5.0, 0),
            make_result(2.0, 5.0, 1),
        )
    )

    assert [result.source_index for result in summary.selected] == [0, 1, 2]


def test_aggregate_results_handles_empty_input() -> None:
    summary = aggregate_results(())

    assert summary.total_count == 0
    assert summary.selected == ()
    assert summary.best_score is None
    assert summary.worst_score is None


def test_aggregate_results_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        aggregate_results((make_result(1.0, 1.0, 0),), limit=0)


def test_aggregate_results_does_not_mutate_input() -> None:
    original = (
        make_result(1.0, 1.0, 0),
        make_result(2.0, 3.0, 1),
    )

    summary = aggregate_results(original)

    assert [result.score for result in original] == [1.0, 3.0]
    assert [result.score for result in summary.selected] == [3.0, 1.0]


def test_aggregate_results_without_limit_returns_all() -> None:
    summary = aggregate_results(
        (
            make_result(1.0, 2.0, 0),
            make_result(2.0, 1.0, 1),
        )
    )

    assert len(summary.selected) == 2
