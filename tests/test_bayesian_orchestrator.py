"""Tests for the L9.7 evidence orchestrator extension."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import EvidenceType
from mh370_inverse_inference.bayesian.negative_search_adapter import (
    NegativeSearchAdapter,
)
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
def expanded_orchestrator() -> EvidenceOrchestrator:
    return EvidenceOrchestrator(
        satcom_adapter=SatcomLikelihoodAdapter(sigma_bto=20.0, sigma_bfo=4.3),
        trajectory_adapter=TrajectoryConsistencyAdapter(sigma_residual=1000.0),
        negative_search_adapter=NegativeSearchAdapter(probability_ceiling=0.9999),
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


def test_legacy_three_channel_path_is_preserved(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    stream = orchestrator.generate_evidence_stream(**sample_payload)
    component_map = {component.evidence_type: component for component in stream}

    assert len(stream) == 3
    assert set(component_map) == {
        EvidenceType.BTO,
        EvidenceType.BFO,
        EvidenceType.TRAJECTORY_CONSISTENCY,
    }
    assert component_map[EvidenceType.BTO].source_id == "ORCHESTRATED-SATCOM-BTO"
    assert component_map[EvidenceType.BFO].source_id == "ORCHESTRATED-SATCOM-BFO"
    assert (
        component_map[EvidenceType.TRAJECTORY_CONSISTENCY].source_id
        == "ORCHESTRATED-TRAJECTORY-CONSISTENCY"
    )


def test_deterministic_adapter_dispatch_and_values(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    stream = orchestrator.generate_evidence_stream(**sample_payload)
    component_map = {component.evidence_type: component for component in stream}
    bto_records = {
        record.hypothesis_id: record.log_likelihood
        for record in component_map[EvidenceType.BTO].records
    }

    expected_peak = -math.log(20.0 * math.sqrt(2.0 * math.pi))
    expected_bto_likelihood = expected_peak - 0.5 * (10.0 / 20.0) ** 2
    assert bto_records["H-1"] == pytest.approx(expected_bto_likelihood)


def test_expanded_four_channel_dispatch_uses_keyed_records(
    expanded_orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    payload = dict(sample_payload)
    payload["detection_probabilities"] = {"H-2": 0.0, "H-1": 0.4}

    stream = expanded_orchestrator.generate_evidence_stream(**payload)
    component_map = {component.evidence_type: component for component in stream}
    search_component = component_map[EvidenceType.NEGATIVE_SEARCH]
    record_map = {
        record.hypothesis_id: record.log_likelihood
        for record in search_component.records
    }

    assert len(stream) == 4
    assert search_component.source_id == "ORCHESTRATED-NEGATIVE-SEARCH"
    assert record_map["H-2"] == 0.0
    assert record_map["H-1"] == pytest.approx(math.log(0.6))


def test_missing_search_adapter_raises_value_error(
    orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    payload = dict(sample_payload)
    payload["detection_probabilities"] = {"H-1": 0.5}

    with pytest.raises(ValueError, match="without an injected"):
        orchestrator.generate_evidence_stream(**payload)


def test_four_channel_sequence_is_repeatable(
    expanded_orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    payload = dict(sample_payload)
    payload["detection_probabilities"] = {"H-1": 0.3, "H-2": 0.7}

    first = expanded_orchestrator.generate_evidence_stream(**payload)
    second = expanded_orchestrator.generate_evidence_stream(**payload)

    assert first == second
    assert tuple(component.evidence_type for component in first) == (
        EvidenceType.BTO,
        EvidenceType.BFO,
        EvidenceType.TRAJECTORY_CONSISTENCY,
        EvidenceType.NEGATIVE_SEARCH,
    )


def test_orchestrator_is_stateless_across_distinct_payloads(
    expanded_orchestrator: EvidenceOrchestrator,
    sample_payload: dict[str, object],
) -> None:
    first_payload = dict(sample_payload)
    first_payload["detection_probabilities"] = {"H-1": 0.3, "H-2": 0.7}
    _ = expanded_orchestrator.generate_evidence_stream(**first_payload)

    isolated_stream = expanded_orchestrator.generate_evidence_stream(
        observed_bto=13000.0,
        observed_bfo=150.0,
        simulated_bto={"H-NEW": 13000.0},
        simulated_bfo={"H-NEW": 150.0},
        trajectory_residuals={"H-NEW": 0.0},
        detection_probabilities={"H-NEW": 0.2},
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
