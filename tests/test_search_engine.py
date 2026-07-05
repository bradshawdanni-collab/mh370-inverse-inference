"""Tests for the deterministic L7 search engine baseline."""

import math
from collections.abc import Mapping

import pytest

from mh370_inverse_inference.search.engine import evaluate_candidates


def score_x(candidate: Mapping[str, float]) -> float:
    return candidate["x"]


def test_evaluate_candidates_orders_by_descending_score() -> None:
    results = evaluate_candidates(
        ({"x": 1.0}, {"x": 3.0}, {"x": 2.0}),
        score_x,
    )

    assert [result.score for result in results] == [3.0, 2.0, 1.0]
    assert [result.as_dict() for result in results] == [
        {"x": 3.0},
        {"x": 2.0},
        {"x": 1.0},
    ]


def test_evaluate_candidates_preserves_generation_order_for_ties() -> None:
    results = evaluate_candidates(
        ({"id": 1.0}, {"id": 2.0}, {"id": 3.0}),
        lambda candidate: 5.0,
    )

    assert [result.source_index for result in results] == [0, 1, 2]
    assert [result.as_dict()["id"] for result in results] == [1.0, 2.0, 3.0]


def test_evaluate_candidates_applies_positive_limit() -> None:
    results = evaluate_candidates(
        ({"x": 1.0}, {"x": 3.0}, {"x": 2.0}),
        score_x,
        limit=2,
    )

    assert [result.score for result in results] == [3.0, 2.0]


def test_evaluate_candidates_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        evaluate_candidates(({"x": 1.0},), score_x, limit=0)


def test_evaluate_candidates_rejects_non_finite_scores() -> None:
    with pytest.raises(ValueError, match="finite"):
        evaluate_candidates(({"x": 1.0},), lambda candidate: math.inf)


def test_evaluate_candidates_does_not_mutate_inputs() -> None:
    candidate = {"x": 2.0, "y": 3.0}

    results = evaluate_candidates((candidate,), lambda item: item["x"] + item["y"])

    assert candidate == {"x": 2.0, "y": 3.0}
    assert results[0].as_dict() == candidate
    assert results[0].as_dict() is not candidate


def test_evaluate_candidates_is_repeatable() -> None:
    candidates = ({"x": 1.0}, {"x": 3.0}, {"x": 2.0})

    first = evaluate_candidates(candidates, score_x)
    second = evaluate_candidates(candidates, score_x)

    assert first == second


def test_evaluate_candidates_accepts_empty_input() -> None:
    assert evaluate_candidates((), score_x) == ()
