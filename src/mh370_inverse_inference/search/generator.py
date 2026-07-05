"""Lazy deterministic candidate generation for bounded search domains."""

from __future__ import annotations

from collections.abc import Iterator
from itertools import product

from mh370_inverse_inference.search.domain import SearchDomain


def iter_candidates(domain: SearchDomain) -> Iterator[dict[str, float]]:
    """Yield ordered candidate dictionaries for every point in the domain grid.

    Dimension order is preserved. The final dimension varies fastest, matching
    the ordering produced by ``itertools.product``.
    """
    index_ranges = tuple(range(dimension.count) for dimension in domain.dimensions)
    for indices in product(*index_ranges):
        yield {
            dimension.name: dimension.value_at(index)
            for dimension, index in zip(domain.dimensions, indices, strict=True)
        }
