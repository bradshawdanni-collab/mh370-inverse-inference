"""Tests for the L9.3 trajectory consistency evidence adapter."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import EvidenceType
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)


@pytest.fixture
def standard_adapter() -> TrajectoryConsistencyAdapter:
    return TrajectoryConsistencyAdapter(sigma_residual=1000.0)


def test_zero_residual_yields_gaussian_peak(
    standard_adapter: TrajectoryConsistencyAdapter,
) -> None:
    component = standard_adapter.evaluate_consistency(
        source_id="KINEMATIC-TRACK-VALIDATION",
        hypothesis_residuals={"H-PERFECT-FIT": 0.0},
    )

    expected_peak = -math.log(1000.0 * math.sqrt(2.0 * math.pi))
    assert component.evidence_type is EvidenceType.TRAJECTORY_CONSISTENCY
    assert component.records[0].log_likelihood == pytest.approx(expected_peak)


def test_symmetric_residuals_receive_identical_penalties(
    standard_adapter: TrajectoryConsistencyAdapter,
) -> None:
    component = standard_adapter.evaluate_consistency(
        source_id="SPATIAL-DRIFT-BOUNDS",
        hypothesis_residuals={
            "H-DRIFT-LEFT": -1000.0,
            "H-DRIFT-RIGHT": 1000.0,
        },
    )
    records = {
        record.hypothesis_id: record.log_likelihood for record in component.records
    }
    expected_peak = -math.log(1000.0 * math.sqrt(2.0 * math.pi))

    assert records["H-DRIFT-LEFT"] == records["H-DRIFT-RIGHT"]
    assert records["H-DRIFT-LEFT"] == pytest.approx(expected_peak - 0.5)


def test_boundary_sorting_enforces_sequence_stability(
    standard_adapter: TrajectoryConsistencyAdapter,
) -> None:
    first = standard_adapter.evaluate_consistency(
        source_id="STABILITY-SORT-TEST",
        hypothesis_residuals={
            "H-GAMMA": 150.0,
            "H-ALPHA": 50.0,
            "H-BRAVO": 200.0,
        },
    )
    second = standard_adapter.evaluate_consistency(
        source_id="STABILITY-SORT-TEST",
        hypothesis_residuals={
            "H-BRAVO": 200.0,
            "H-GAMMA": 150.0,
            "H-ALPHA": 50.0,
        },
    )

    assert first == second
    assert tuple(record.hypothesis_id for record in first.records) == (
        "H-ALPHA",
        "H-BRAVO",
        "H-GAMMA",
    )


def test_adapter_is_immutable() -> None:
    adapter = TrajectoryConsistencyAdapter(sigma_residual=1000.0)

    with pytest.raises(FrozenInstanceError):
        adapter.sigma_residual = 500.0


@pytest.mark.parametrize("sigma", [0.0, -1.0, float("inf"), float("nan")])
def test_invalid_sigma_fails_closed(sigma: float) -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        TrajectoryConsistencyAdapter(sigma_residual=sigma)


@pytest.mark.parametrize(
    ("source_id", "residuals", "message"),
    [
        ("", {"H-1": 0.0}, "source_id"),
        ("TRACK", {}, "cannot be empty"),
        ("TRACK", {"": 0.0}, "identifiers"),
        ("TRACK", {"H-1": float("inf")}, "must be finite"),
        ("TRACK", {"H-1": float("nan")}, "must be finite"),
    ],
)
def test_invalid_inputs_fail_closed(
    source_id: str,
    residuals: dict[str, float],
    message: str,
) -> None:
    adapter = TrajectoryConsistencyAdapter(sigma_residual=1000.0)

    with pytest.raises(ValueError, match=message):
        adapter.evaluate_consistency(
            source_id=source_id,
            hypothesis_residuals=residuals,
        )
