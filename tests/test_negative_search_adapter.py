"""Tests for the L9.6 negative-search evidence adapter."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import EvidenceType
from mh370_inverse_inference.bayesian.negative_search_adapter import (
    NegativeSearchAdapter,
)


@pytest.fixture
def default_adapter() -> NegativeSearchAdapter:
    return NegativeSearchAdapter()


def test_zero_detection_probability_yields_zero_penalty(
    default_adapter: NegativeSearchAdapter,
) -> None:
    component = default_adapter.evaluate_negative_search(
        source_id="SEARCH-SECTOR-A",
        detection_probabilities={"H-OPEN": 0.0},
    )

    assert component.evidence_type is EvidenceType.NEGATIVE_SEARCH
    assert component.records[0].log_likelihood == 0.0


def test_increasing_detection_probability_monotonically_reduces_support(
    default_adapter: NegativeSearchAdapter,
) -> None:
    component = default_adapter.evaluate_negative_search(
        source_id="SEARCH-SECTOR-A",
        detection_probabilities={
            "H-LOW": 0.1,
            "H-MEDIUM": 0.5,
            "H-HIGH": 0.9,
        },
    )
    scores = {
        record.hypothesis_id: record.log_likelihood for record in component.records
    }

    assert scores["H-LOW"] > scores["H-MEDIUM"] > scores["H-HIGH"]


def test_probability_one_is_intercepted_by_policy_ceiling(
    default_adapter: NegativeSearchAdapter,
) -> None:
    component = default_adapter.evaluate_negative_search(
        source_id="SEARCH-SECTOR-A",
        detection_probabilities={"H-IMPOSSIBLE-PERFECTION": 1.0},
    )

    expected = math.log(default_adapter.likelihood_floor)
    assert component.records[0].log_likelihood == pytest.approx(expected)
    assert math.isfinite(component.records[0].log_likelihood)


def test_mapping_order_does_not_change_output(
    default_adapter: NegativeSearchAdapter,
) -> None:
    first = default_adapter.evaluate_negative_search(
        source_id="SEARCH-SECTOR-A",
        detection_probabilities={"H-2": 0.8, "H-1": 0.2},
    )
    second = default_adapter.evaluate_negative_search(
        source_id="SEARCH-SECTOR-A",
        detection_probabilities={"H-1": 0.2, "H-2": 0.8},
    )

    assert first == second
    assert tuple(record.hypothesis_id for record in first.records) == ("H-1", "H-2")


def test_adapter_is_immutable() -> None:
    adapter = NegativeSearchAdapter()

    with pytest.raises(FrozenInstanceError):
        adapter.likelihood_floor = 1e-6


@pytest.mark.parametrize(
    ("probability_ceiling", "likelihood_floor", "message"),
    [
        (0.0, 1e-12, "probability_ceiling"),
        (1.0, 1e-12, "probability_ceiling"),
        (float("nan"), 1e-12, "probability_ceiling"),
        (0.9, 0.0, "likelihood_floor"),
        (0.9, 2.0, "likelihood_floor"),
    ],
)
def test_invalid_configuration_fails_closed(
    probability_ceiling: float,
    likelihood_floor: float,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        NegativeSearchAdapter(
            probability_ceiling=probability_ceiling,
            likelihood_floor=likelihood_floor,
        )


@pytest.mark.parametrize(
    ("source_id", "probabilities", "message"),
    [
        ("", {"H-1": 0.2}, "source_id"),
        ("SEARCH", {}, "cannot be empty"),
        ("SEARCH", {"": 0.2}, "identifiers"),
        ("SEARCH", {"H-1": float("nan")}, "must be finite"),
        ("SEARCH", {"H-1": -0.1}, "within"),
        ("SEARCH", {"H-1": 1.1}, "within"),
    ],
)
def test_invalid_inputs_fail_closed(
    source_id: str,
    probabilities: dict[str, float],
    message: str,
) -> None:
    adapter = NegativeSearchAdapter()

    with pytest.raises(ValueError, match=message):
        adapter.evaluate_negative_search(
            source_id=source_id,
            detection_probabilities=probabilities,
        )
