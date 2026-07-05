"""Frozen end-to-end integration test for the deterministic L7 search stack."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.search.domain import SearchDimension, SearchDomain
from mh370_inverse_inference.search.engine import evaluate_candidates
from mh370_inverse_inference.search.generator import iter_candidates
from mh370_inverse_inference.search.results import aggregate_results


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "search"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_frozen_deterministic_search_pipeline() -> None:
    input_data = load_json("case_001.input.json")
    expected = load_json("case_001.expected.json")
    metadata = load_json("case_001.meta.json")

    domain = SearchDomain(
        dimensions=tuple(
            SearchDimension(
                name=dimension["name"],
                lower=dimension["lower"],
                upper=dimension["upper"],
                step=dimension["step"],
            )
            for dimension in input_data["dimensions"]
        )
    )
    reference_point = input_data["reference_point"]

    def score(candidate: Mapping[str, float]) -> float:
        return -sum(
            (candidate[name] - reference_point[name]) ** 2
            for name in domain.names
        )

    first_results = evaluate_candidates(iter_candidates(domain), score)
    second_results = evaluate_candidates(iter_candidates(domain), score)
    summary = aggregate_results(first_results, limit=input_data["top_n"])

    assert metadata["fixture_id"] == input_data["fixture_id"]
    assert expected["fixture_id"] == input_data["fixture_id"]
    assert metadata["randomness"] == "none"
    assert first_results == second_results
    assert summary.total_count == expected["candidate_count"]
    assert summary.best_score == pytest.approx(
        expected["best_score"], abs=metadata["numeric_tolerance"]
    )
    assert summary.worst_score == pytest.approx(
        expected["worst_score"], abs=metadata["numeric_tolerance"]
    )
    assert [
        {
            "candidate": result.as_dict(),
            "score": result.score,
            "source_index": result.source_index,
        }
        for result in summary.selected
    ] == expected["selected"]
