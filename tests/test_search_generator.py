"""Tests for deterministic L7 candidate generation."""

from mh370_inverse_inference.search.domain import SearchDimension, SearchDomain
from mh370_inverse_inference.search.generator import iter_candidates


def test_iter_candidates_emits_expected_order() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="heading", lower=0.0, upper=10.0, step=10.0),
            SearchDimension(name="speed", lower=200.0, upper=220.0, step=10.0),
        )
    )

    assert list(iter_candidates(domain)) == [
        {"heading": 0.0, "speed": 200.0},
        {"heading": 0.0, "speed": 210.0},
        {"heading": 0.0, "speed": 220.0},
        {"heading": 10.0, "speed": 200.0},
        {"heading": 10.0, "speed": 210.0},
        {"heading": 10.0, "speed": 220.0},
    ]


def test_iter_candidates_matches_domain_candidate_count() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="x", lower=0.0, upper=2.0, step=1.0),
            SearchDimension(name="y", lower=10.0, upper=20.0, step=5.0),
            SearchDimension(name="z", lower=-1.0, upper=1.0, step=1.0),
        )
    )

    assert len(list(iter_candidates(domain))) == domain.candidate_count


def test_iter_candidates_is_repeatable() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="heading", lower=0.0, upper=5.0, step=5.0),
            SearchDimension(name="speed", lower=200.0, upper=210.0, step=10.0),
        )
    )

    first = list(iter_candidates(domain))
    second = list(iter_candidates(domain))

    assert first == second


def test_iter_candidates_handles_zero_width_dimension() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="fixed", lower=5.0, upper=5.0, step=1.0),
            SearchDimension(name="variable", lower=0.0, upper=1.0, step=1.0),
        )
    )

    assert list(iter_candidates(domain)) == [
        {"fixed": 5.0, "variable": 0.0},
        {"fixed": 5.0, "variable": 1.0},
    ]


def test_iter_candidates_returns_fresh_dictionaries() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="x", lower=0.0, upper=1.0, step=1.0),
        )
    )

    candidates = list(iter_candidates(domain))
    candidates[0]["x"] = 99.0

    assert candidates[1] == {"x": 1.0}
