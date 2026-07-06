"""Tests for the L10.5 deterministic reference engine."""

import copy
import json
from pathlib import Path

import pytest

from mh370_inverse_inference.engine.contract import EngineStatus
from mh370_inverse_inference.engine.reference import run_reference_engine
from mh370_inverse_inference.engine.hashing import sha256_payload

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "bayesian"
FIXTURE_PATH = FIXTURE_DIR / "case_001.input.json"
EXPECTED_PATH = FIXTURE_DIR / "case_001.expected.json"


def load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    assert isinstance(loaded, dict)
    return loaded


def test_reference_engine_matches_frozen_l9_fixture() -> None:
    response = run_reference_engine(FIXTURE_PATH)
    expected = load_json(EXPECTED_PATH)
    expected_map = {
        str(entry["hypothesis_id"]): entry for entry in expected["posteriors"]
    }

    assert response.status is EngineStatus.SUCCESS
    assert response.argmax_hypothesis_id == "H-001"
    assert len(response.posterior_distribution) == len(expected_map)
    for result in response.posterior_distribution:
        reference = expected_map[result.hypothesis_id]
        assert result.probability == pytest.approx(
            float(reference["posterior_probability"]),
            abs=1e-12,
        )


def test_reference_engine_is_replay_deterministic() -> None:
    first = run_reference_engine(FIXTURE_PATH)
    second = run_reference_engine(FIXTURE_PATH)

    assert first == second
    assert first.replay_hash == second.replay_hash
    assert [step.output_hash for step in first.trace] == [
        step.output_hash for step in second.trace
    ]


def test_reference_engine_trace_order_is_fixed() -> None:
    response = run_reference_engine(FIXTURE_PATH)

    assert [step.step_id for step in response.trace] == [
        "adapter_normalization",
        "likelihood_evaluation",
        "fusion",
        "constraint_application",
        "normalization",
    ]


def test_reference_engine_probability_mass_invariants() -> None:
    response = run_reference_engine(FIXTURE_PATH)
    total = sum(item.probability for item in response.posterior_distribution)

    assert total == pytest.approx(1.0, abs=1e-12)
    assert response.normalization_error <= 1e-12
    assert response.pre_normalization_mass == pytest.approx(1.0, abs=1e-12)


def test_mutated_fixture_changes_replay_hash(tmp_path: Path) -> None:
    fixture = load_json(FIXTURE_PATH)
    mutated = copy.deepcopy(fixture)
    simulations = mutated["simulations"]
    assert isinstance(simulations, dict)
    detection_probabilities = simulations["detection_probabilities"]
    assert isinstance(detection_probabilities, dict)
    detection_probabilities["H-001"] = 0.4

    mutated_path = tmp_path / "case_001.input.json"
    mutated_path.write_text(json.dumps(mutated), encoding="utf-8")

    original_response = run_reference_engine(FIXTURE_PATH)
    mutated_response = run_reference_engine(mutated_path)

    assert original_response.replay_hash != mutated_response.replay_hash


def test_reference_engine_trace_hashes_are_valid_sha256() -> None:
    response = run_reference_engine(FIXTURE_PATH)

    assert len(response.replay_hash) == 64
    for step in response.trace:
        assert len(step.input_hash) == 64
        assert len(step.output_hash) == 64
        assert len(step.op_signature_hash) == 64


def test_response_replay_hash_depends_on_final_posterior_payload() -> None:
    response = run_reference_engine(FIXTURE_PATH)
    posterior_payload = tuple(
        {
            "hypothesis_id": item.hypothesis_id,
            "probability": item.probability,
        }
        for item in response.posterior_distribution
    )

    assert sha256_payload(posterior_payload) != response.replay_hash
