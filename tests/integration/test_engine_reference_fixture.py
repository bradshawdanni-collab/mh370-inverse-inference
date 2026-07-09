"""Integration fixture tests for the L10.5 reference engine response shape."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.engine.reference import run_reference_engine

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"
INPUT_PATH = FIXTURE_DIR / "bayesian" / "case_001.input.json"
EXPECTED_PATH = FIXTURE_DIR / "engine" / "reference_case_001.expected.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HASH_PLACEHOLDER = "<sha256>"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    assert isinstance(loaded, dict)
    return loaded


def normalize_hash(value: str) -> str:
    """Replace a concrete SHA-256 digest with the release-fixture placeholder."""
    if SHA256_RE.fullmatch(value):
        return HASH_PLACEHOLDER
    return value


def response_snapshot() -> dict[str, Any]:
    """Build the normalized public response snapshot for fixture comparison."""
    response = run_reference_engine(INPUT_PATH)
    return {
        "argmax_hypothesis_id": response.argmax_hypothesis_id,
        "contract_version": response.contract_version,
        "engine_version": response.engine_version,
        "normalization_error": response.normalization_error,
        "posterior_distribution": [
            {
                "hypothesis_id": item.hypothesis_id,
                "probability": item.probability,
            }
            for item in response.posterior_distribution
        ],
        "pre_normalization_mass": response.pre_normalization_mass,
        "replay_hash": normalize_hash(response.replay_hash),
        "request_id": response.request_id,
        "status": response.status.value,
        "trace": [
            {
                "duration_ms": step.duration_ms,
                "input_hash": normalize_hash(step.input_hash),
                "op_signature_hash": normalize_hash(step.op_signature_hash),
                "operation": step.operation.value,
                "output_hash": normalize_hash(step.output_hash),
                "step_id": step.step_id,
            }
            for step in response.trace
        ],
    }


def test_reference_engine_response_matches_release_fixture() -> None:
    """Assert the normalized reference response shape remains frozen."""
    assert response_snapshot() == load_json(EXPECTED_PATH)


def test_reference_engine_hashes_are_present_and_well_formed() -> None:
    """Validate concrete hashes separately from the normalized snapshot."""
    response = run_reference_engine(INPUT_PATH)

    assert SHA256_RE.fullmatch(response.replay_hash)
    for step in response.trace:
        assert SHA256_RE.fullmatch(step.input_hash)
        assert SHA256_RE.fullmatch(step.output_hash)
        assert SHA256_RE.fullmatch(step.op_signature_hash)


def test_reference_engine_posterior_values_remain_frozen() -> None:
    """Assert the canonical L9 posterior baseline is still represented exactly."""
    response = run_reference_engine(INPUT_PATH)
    posterior: dict[str, float] = {}
    for item in response.posterior_distribution:
        posterior[item.hypothesis_id] = item.probability

    assert posterior["H-001"] == pytest.approx(0.5835928759344674, abs=1e-12)
    assert posterior["H-002"] == pytest.approx(0.4164071240655326, abs=1e-12)
    assert sum(posterior.values()) == pytest.approx(1.0, abs=1e-12)


def test_reference_engine_stage_order_remains_frozen() -> None:
    """Assert the release fixture freezes the canonical stage sequence."""
    response = run_reference_engine(INPUT_PATH)

    assert [step.step_id for step in response.trace] == [
        "adapter_normalization",
        "likelihood_evaluation",
        "fusion",
        "constraint_application",
        "normalization",
    ]
