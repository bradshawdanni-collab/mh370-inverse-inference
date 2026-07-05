"""Tests for deterministic L7 search-domain primitives."""

import pytest

from mh370_inverse_inference.search.domain import SearchDimension, SearchDomain


def test_search_dimension_count_and_values_are_deterministic() -> None:
    dimension = SearchDimension(name="heading", lower=0.0, upper=10.0, step=2.5)

    assert dimension.count == 5
    assert [dimension.value_at(index) for index in range(dimension.count)] == [
        0.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ]


def test_search_dimension_inclusive_count_excludes_overshoot() -> None:
    dimension = SearchDimension(name="speed", lower=0.0, upper=10.0, step=3.0)

    assert dimension.count == 4
    assert dimension.value_at(3) == 9.0


def test_search_dimension_validation_fails_closed() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        SearchDimension(name="", lower=0.0, upper=1.0, step=0.5)

    with pytest.raises(ValueError, match="greater than or equal"):
        SearchDimension(name="bad", lower=2.0, upper=1.0, step=0.5)

    with pytest.raises(ValueError, match="positive"):
        SearchDimension(name="bad", lower=0.0, upper=1.0, step=0.0)


def test_search_dimension_normalize_maps_to_unit_interval() -> None:
    dimension = SearchDimension(name="altitude", lower=100.0, upper=200.0, step=50.0)

    assert dimension.normalize(100.0) == 0.0
    assert dimension.normalize(150.0) == 0.5
    assert dimension.normalize(200.0) == 1.0


def test_search_dimension_normalize_rejects_out_of_bounds() -> None:
    dimension = SearchDimension(name="altitude", lower=100.0, upper=200.0, step=50.0)

    with pytest.raises(ValueError, match="within"):
        dimension.normalize(250.0)


def test_zero_width_dimension_normalizes_to_zero() -> None:
    dimension = SearchDimension(name="fixed", lower=5.0, upper=5.0, step=1.0)

    assert dimension.count == 1
    assert dimension.normalize(5.0) == 0.0


def test_search_domain_preserves_dimension_order_and_candidate_count() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="heading", lower=0.0, upper=10.0, step=5.0),
            SearchDimension(name="speed", lower=200.0, upper=220.0, step=10.0),
        )
    )

    assert domain.names == ("heading", "speed")
    assert domain.candidate_count == 9


def test_search_domain_rejects_duplicate_dimension_names() -> None:
    with pytest.raises(ValueError, match="unique"):
        SearchDomain(
            dimensions=(
                SearchDimension(name="x", lower=0.0, upper=1.0, step=1.0),
                SearchDimension(name="x", lower=0.0, upper=1.0, step=1.0),
            )
        )


def test_search_domain_normalize_point_requires_exact_keys() -> None:
    domain = SearchDomain(
        dimensions=(SearchDimension(name="heading", lower=0.0, upper=10.0, step=5.0),)
    )

    with pytest.raises(ValueError, match="exactly"):
        domain.normalize_point({"speed": 1.0})


def test_search_domain_normalize_point_uses_dimension_order() -> None:
    domain = SearchDomain(
        dimensions=(
            SearchDimension(name="heading", lower=0.0, upper=10.0, step=5.0),
            SearchDimension(name="speed", lower=200.0, upper=220.0, step=10.0),
        )
    )

    assert domain.normalize_point({"speed": 210.0, "heading": 5.0}) == {
        "heading": 0.5,
        "speed": 0.5,
    }
