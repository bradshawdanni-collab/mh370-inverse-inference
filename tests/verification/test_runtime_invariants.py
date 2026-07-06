"""Runtime invariant checks for deterministic Bayesian replay tooling."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from mh370_inverse_inference.verification.replay import (
    BayesianReplayRunner,
    compare_artifacts,
    load_json,
    sha256_payload,
    verify_fixture_hashes,
)

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "bayesian"


def test_fixture_hashes_validate_against_metadata() -> None:
    verify_fixture_hashes(FIXTURE_DIR)


def test_repeated_replay_produces_identical_artifacts() -> None:
    runner = BayesianReplayRunner(FIXTURE_DIR)

    first = runner.run()
    second = runner.run()

    assert first == second
    assert compare_artifacts(first, second) == ()
    assert first.hashes["artifact"] == second.hashes["artifact"]


def test_replay_artifact_matches_frozen_expected_output() -> None:
    artifact = BayesianReplayRunner(FIXTURE_DIR).run()
    expected = load_json(FIXTURE_DIR / "case_001.expected.json")
    expected_map = {item["hypothesis_id"]: item for item in expected["posteriors"]}

    assert artifact.case_id == expected["case_id"]
    assert {entry["hypothesis_id"] for entry in artifact.posteriors} == set(
        expected_map
    )
    for entry in artifact.posteriors:
        reference = expected_map[entry["hypothesis_id"]]
        assert entry["prior_weight"] == reference["prior_weight"]
        assert entry["joint_log_score"] == pytest.approx(
            reference["joint_log_score"], abs=1e-12
        )
        assert entry["posterior_probability"] == pytest.approx(
            reference["posterior_probability"], abs=1e-12
        )


def test_evidence_order_and_hashes_are_stable() -> None:
    artifact = BayesianReplayRunner(FIXTURE_DIR).run()

    evidence_types = [
        component["evidence_type"] for component in artifact.evidence_components
    ]
    assert evidence_types == [
        "bto",
        "bfo",
        "trajectory_consistency",
        "negative_search",
    ]
    assert artifact.hashes["evidence"] == sha256_payload(
        artifact.evidence_components
    )
    assert artifact.hashes["posterior"] == sha256_payload(artifact.posteriors)


def test_input_fixture_is_not_mutated_by_replay() -> None:
    before = copy.deepcopy(load_json(FIXTURE_DIR / "case_001.input.json"))

    _ = BayesianReplayRunner(FIXTURE_DIR).run()

    after = load_json(FIXTURE_DIR / "case_001.input.json")
    assert after == before
