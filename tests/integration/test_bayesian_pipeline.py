"""Integration tests for the frozen Bayesian fixture."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.bayesian.contract import (
    Hypothesis,
    fuse_evidence,
)
from mh370_inverse_inference.bayesian.orchestrator import (
    EvidenceOrchestrator,
)
from mh370_inverse_inference.bayesian.satcom_adapter import (
    SatcomLikelihoodAdapter,
)
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "bayesian"


def load_fixture(filename: str) -> dict[str, Any]:
    with (FIXTURE_DIR / filename).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def fixture_hash(filename: str) -> str:
    return hashlib.sha256((FIXTURE_DIR / filename).read_bytes()).hexdigest()


def test_fixture_structural_integrity() -> None:
    meta = load_fixture("case_001.meta.json")
    inputs = load_fixture("case_001.input.json")
    expected = load_fixture("case_001.expected.json")

    assert meta["case_id"] == inputs["case_id"] == expected["case_id"]
    assert meta["schema_version"] == "L9.1-v1.0.0"

    input_ids = {item["hypothesis_id"] for item in inputs["hypotheses"]}
    expected_ids = {item["hypothesis_id"] for item in expected["posteriors"]}
    assert input_ids == expected_ids

    for filename, expected_hash in meta["fixture_hashes"].items():
        assert fixture_hash(filename) == expected_hash


def test_end_to_end_pipeline_matches_frozen_fixture() -> None:
    inputs = load_fixture("case_001.input.json")
    expected = load_fixture("case_001.expected.json")

    hypotheses = tuple(
        Hypothesis(
            hypothesis_id=item["hypothesis_id"],
            prior_weight=item["prior_weight"],
        )
        for item in inputs["hypotheses"]
    )
    parameters = inputs["parameters"]
    observations = inputs["observations"]
    simulations = inputs["simulations"]

    orchestrator = EvidenceOrchestrator(
        satcom_adapter=SatcomLikelihoodAdapter(
            sigma_bto=parameters["sigma_bto"],
            sigma_bfo=parameters["sigma_bfo"],
        ),
        trajectory_adapter=TrajectoryConsistencyAdapter(
            sigma_residual=parameters["sigma_residual"]
        ),
    )
    evidence = orchestrator.generate_evidence_stream(
        observed_bto=observations["observed_bto"],
        observed_bfo=observations["observed_bfo"],
        simulated_bto=simulations["simulated_bto"],
        simulated_bfo=simulations["simulated_bfo"],
        trajectory_residuals=simulations["trajectory_residuals"],
    )
    results = fuse_evidence(hypotheses, evidence)

    expected_map = {item["hypothesis_id"]: item for item in expected["posteriors"]}
    assert {entry.hypothesis_id for entry in results} == set(expected_map)

    for entry in results:
        reference = expected_map[entry.hypothesis_id]
        assert entry.prior_weight == reference["prior_weight"]
        assert entry.joint_log_score == pytest.approx(
            reference["joint_log_score"], abs=1e-12
        )
        assert entry.posterior_probability == pytest.approx(
            reference["posterior_probability"], abs=1e-12
        )

    total_probability = sum(entry.posterior_probability for entry in results)
    assert total_probability == pytest.approx(1.0, abs=1e-15)
