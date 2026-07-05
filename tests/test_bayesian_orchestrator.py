"""Tests for the L9.4 evidence scoring orchestrator."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import EvidenceType
from mh370_inverse_inference.bayesian.orchestrator import EvidenceOrchestrator
from mh370_inverse_inference.bayesian.satcom_adapter import SatcomLikelihoodAdapter
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)


@pytest.fixture
def orchestrator() -> EvidenceOrchestrator:
    return EvidenceOrchestrator(
        satcom_adapter=SatcomLikelihoodAdapter(sigma_bto=20.0, sigma_bfo=4.3),
        trajectory_adapter=TrajectoryConsistencyAdapter(sigma_residual=1000.0),
    )


@pytest.fixture
def sample_payload() -> dict[str, object]:
    return {
        "observed_bto": 12500.0,
        "observed_bfo": 140.0,
        "simulated_bto": {"H-1": 12510.0, "H-2": 12490.0},
        "simulated_bfo": {"H-1": 142.0, "H-2": 138.0},
        "trajectory_residuals": {"H-1": 250.0, "H-2": 800.0},
    }


def test_deterministic_adapter_dispatch_and_values(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    stream = orchestrator.generate_evidence_stream(**sample_payload)

    assert tuple(component.source_id for component in stream) == (
        "ORCHESTRATED-SATCOM-BTO",
        "ORCHESTRATED-SATCOM-BFO",
        "ORCHESTRATED-TRAJECTORY-CONSISTENCY",
    )
    assert tuple(component.evidence_type for component in stream) == (
        EvidenceType.BTO,
        EvidenceType.BFO,
        EvidenceType.TRAJECTORY_CONSISTENCY,
    )

    expected_peak = -math.log(20.0 * math.sqrt(2.0 * math.pi))
    expected_bto_likelihood = expected_peak - 0.5 * (10.0 / 20.0) ** 2
    assert stream[0].records[0].hypothesis_id == "H-1"
    assert stream[0].records[0].log_likelihood == pytest.approx(
        expected_bto_likelihood
    )


def test_sequence_order_is_invariant(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    first = orchestrator.generate_evidence_stream(**sample_payload)
    second = orchestrator.generate_evidence_stream(**sample_payload)

    assert first == second
    assert tuple(component.source_id for component in first) == tuple(
        component.source_id for component in second
    )
    assert first[0].records == second[0].records


def test_orchestrator_is_stateless_across_distinct_payloads(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    _ = orchestrator.generate_evidence_stream(**sample_payload)

    isolated_stream = orchestrator.generate_evidence_stream(
        observed_bto=13000.0,
        observed_bfo=150.0,
        simulated_bto={"H-NEW": 13000.0},
        simulated_bfo={"H-NEW": 150.0},
        trajectory_residuals={"H-NEW": 0.0},
    )

    for component in isolated_stream:
        ids = tuple(record.hypothesis_id for record in component.records)
        assert ids == ("H-NEW",)


def test_orchestrator_configuration_is_immutable(
    orchestrator: EvidenceOrchestrator,
) -> None:
    with pytest.raises(FrozenInstanceError):
        orchestrator.satcom_adapter = SatcomLikelihoodAdapter(
            sigma_bto=1.0,
            sigma_bfo=1.0,
        )


def test_adapter_validation_errors_propagate(
    orchestrator: EvidenceOrchestrator,
) -> None:
    with pytest.raises(ValueError, match="observed"):
        orchestrator.generate_evidence_stream(
            observed_bto=float("nan"),
            observed_bfo=150.0,
            simulated_bto={"H-1": 13000.0},
            simulated_bfo={"H-1": 150.0},
            trajectory_residuals={"H-1": 0.0},
        )
