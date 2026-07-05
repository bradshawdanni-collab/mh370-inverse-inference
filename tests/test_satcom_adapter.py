"""Tests for the L9.2 SATCOM Gaussian likelihood adapters."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import EvidenceType
from mh370_inverse_inference.bayesian.satcom_adapter import SatcomLikelihoodAdapter


@pytest.fixture
def default_adapter() -> SatcomLikelihoodAdapter:
    return SatcomLikelihoodAdapter(sigma_bto=20.0, sigma_bfo=4.3)


def test_perfect_bto_match_yields_gaussian_peak(
    default_adapter: SatcomLikelihoodAdapter,
) -> None:
    component = default_adapter.evaluate_bto_component(
        source_id="INMARSAT-BTO-PING-1",
        observed_bto=12500.0,
        hypothesis_simulations={"H-TRACK-A": 12500.0},
    )

    expected_peak = -math.log(20.0 * math.sqrt(2.0 * math.pi))
    assert component.evidence_type is EvidenceType.BTO
    assert component.records[0].log_likelihood == pytest.approx(expected_peak)


def test_bto_equal_and_opposite_residuals_are_symmetric(
    default_adapter: SatcomLikelihoodAdapter,
) -> None:
    component = default_adapter.evaluate_bto_component(
        source_id="INMARSAT-BTO-PING-1",
        observed_bto=12500.0,
        hypothesis_simulations={
            "H-SHORT": 12480.0,
            "H-LONG": 12520.0,
        },
    )
    records = {
        record.hypothesis_id: record.log_likelihood for record in component.records
    }
    expected_peak = -math.log(20.0 * math.sqrt(2.0 * math.pi))

    assert records["H-SHORT"] == records["H-LONG"]
    assert records["H-SHORT"] == pytest.approx(expected_peak - 0.5)


def test_bfo_component_uses_bfo_contract_type_and_sigma(
    default_adapter: SatcomLikelihoodAdapter,
) -> None:
    component = default_adapter.evaluate_bfo_component(
        source_id="INMARSAT-BFO-PING-1",
        observed_bfo=100.0,
        hypothesis_simulations={"H-1": 104.3},
    )
    expected_peak = -math.log(4.3 * math.sqrt(2.0 * math.pi))

    assert component.evidence_type is EvidenceType.BFO
    assert component.records[0].log_likelihood == pytest.approx(expected_peak - 0.5)


def test_record_order_is_deterministic_across_mapping_order(
    default_adapter: SatcomLikelihoodAdapter,
) -> None:
    first = default_adapter.evaluate_bto_component(
        source_id="BTO",
        observed_bto=0.0,
        hypothesis_simulations={"H-2": 2.0, "H-1": 1.0},
    )
    second = default_adapter.evaluate_bto_component(
        source_id="BTO",
        observed_bto=0.0,
        hypothesis_simulations={"H-1": 1.0, "H-2": 2.0},
    )

    assert first == second
    assert tuple(record.hypothesis_id for record in first.records) == ("H-1", "H-2")


def test_adapter_is_immutable() -> None:
    adapter = SatcomLikelihoodAdapter(sigma_bto=20.0, sigma_bfo=4.3)

    with pytest.raises(FrozenInstanceError):
        adapter.sigma_bto = 10.0


@pytest.mark.parametrize(
    ("sigma_bto", "sigma_bfo"),
    [
        (0.0, 4.3),
        (-1.0, 4.3),
        (20.0, float("inf")),
        (float("nan"), 4.3),
    ],
)
def test_invalid_sigmas_fail_closed(sigma_bto: float, sigma_bfo: float) -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        SatcomLikelihoodAdapter(sigma_bto=sigma_bto, sigma_bfo=sigma_bfo)


@pytest.mark.parametrize(
    ("source_id", "observed", "simulations", "message"),
    [
        ("", 0.0, {"H-1": 0.0}, "source_id"),
        ("BTO", float("nan"), {"H-1": 0.0}, "observed"),
        ("BTO", 0.0, {}, "cannot be empty"),
        ("BTO", 0.0, {"": 0.0}, "identifiers"),
        ("BTO", 0.0, {"H-1": float("inf")}, "simulated"),
    ],
)
def test_invalid_measurement_inputs_fail_closed(
    source_id: str,
    observed: float,
    simulations: dict[str, float],
    message: str,
) -> None:
    adapter = SatcomLikelihoodAdapter(sigma_bto=20.0, sigma_bfo=4.3)

    with pytest.raises(ValueError, match=message):
        adapter.evaluate_bto_component(
            source_id=source_id,
            observed_bto=observed,
            hypothesis_simulations=simulations,
        )
