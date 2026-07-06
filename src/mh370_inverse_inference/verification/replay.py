"""Deterministic replay helpers for the Bayesian evidence fixture."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    Hypothesis,
    fuse_evidence,
)
from mh370_inverse_inference.bayesian.negative_search_adapter import (
    NegativeSearchAdapter,
)
from mh370_inverse_inference.bayesian.orchestrator import EvidenceOrchestrator
from mh370_inverse_inference.bayesian.satcom_adapter import SatcomLikelihoodAdapter
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReplayArtifact:
    """Canonical replay output for one Bayesian fixture execution."""

    case_id: str
    schema_version: str
    evidence_components: tuple[JsonObject, ...]
    posteriors: tuple[JsonObject, ...]
    hashes: Mapping[str, str]

    def as_dict(self) -> JsonObject:
        """Return a JSON-serializable representation."""
        return {
            "case_id": self.case_id,
            "schema_version": self.schema_version,
            "evidence_components": list(self.evidence_components),
            "posteriors": list(self.posteriors),
            "hashes": dict(self.hashes),
        }


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize payload into deterministic JSON bytes for hashing."""
    return json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    """Return the SHA-256 digest for a canonical JSON payload."""
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def load_json(path: Path) -> JsonObject:
    """Load one JSON object from disk."""
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    if not isinstance(loaded, dict):
        raise ValueError(f"fixture {path} must contain a JSON object")
    return loaded


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_fixture_hashes(fixture_dir: Path) -> None:
    """Validate fixture file hashes against case metadata."""
    metadata = load_json(fixture_dir / "case_001.meta.json")
    fixture_hashes = metadata["fixture_hashes"]
    if not isinstance(fixture_hashes, dict):
        raise ValueError("fixture_hashes must be a JSON object")
    for filename, expected_hash in fixture_hashes.items():
        if not isinstance(filename, str) or not isinstance(expected_hash, str):
            raise ValueError("fixture_hashes must map strings to strings")
        actual_hash = file_sha256(fixture_dir / filename)
        if actual_hash != expected_hash:
            raise ValueError(f"fixture hash mismatch for {filename}")


def _as_float_mapping(value: object, name: str) -> Mapping[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return {str(key): float(raw_value) for key, raw_value in value.items()}


def _summarize_component(component: EvidenceComponent) -> JsonObject:
    return {
        "evidence_type": component.evidence_type.value,
        "source_id": component.source_id,
        "records": [
            {
                "hypothesis_id": record.hypothesis_id,
                "log_likelihood": record.log_likelihood,
            }
            for record in component.records
        ],
    }


def _summarize_posterior(results: Sequence[Any]) -> tuple[JsonObject, ...]:
    return tuple(
        {
            "hypothesis_id": result.hypothesis_id,
            "prior_weight": result.prior_weight,
            "joint_log_score": result.joint_log_score,
            "posterior_probability": result.posterior_probability,
        }
        for result in results
    )


class BayesianReplayRunner:
    """Replay the frozen Bayesian fixture through production code."""

    def __init__(self, fixture_dir: Path) -> None:
        self.fixture_dir = fixture_dir

    def run(self) -> ReplayArtifact:
        """Execute one deterministic replay and return a canonical artifact."""
        verify_fixture_hashes(self.fixture_dir)
        metadata = load_json(self.fixture_dir / "case_001.meta.json")
        inputs = load_json(self.fixture_dir / "case_001.input.json")

        hypotheses = tuple(
            Hypothesis(
                hypothesis_id=str(item["hypothesis_id"]),
                prior_weight=float(item["prior_weight"]),
            )
            for item in inputs["hypotheses"]
        )
        parameters = inputs["parameters"]
        observations = inputs["observations"]
        simulations = inputs["simulations"]

        orchestrator = EvidenceOrchestrator(
            satcom_adapter=SatcomLikelihoodAdapter(
                sigma_bto=float(parameters["sigma_bto"]),
                sigma_bfo=float(parameters["sigma_bfo"]),
            ),
            trajectory_adapter=TrajectoryConsistencyAdapter(
                sigma_residual=float(parameters["sigma_residual"])
            ),
            negative_search_adapter=NegativeSearchAdapter(
                probability_ceiling=float(parameters["probability_ceiling"]),
                likelihood_floor=float(parameters["likelihood_floor"]),
            ),
        )
        evidence_components = orchestrator.generate_evidence_stream(
            observed_bto=float(observations["observed_bto"]),
            observed_bfo=float(observations["observed_bfo"]),
            simulated_bto=_as_float_mapping(
                simulations["simulated_bto"], "simulated_bto"
            ),
            simulated_bfo=_as_float_mapping(
                simulations["simulated_bfo"], "simulated_bfo"
            ),
            trajectory_residuals=_as_float_mapping(
                simulations["trajectory_residuals"], "trajectory_residuals"
            ),
            detection_probabilities=_as_float_mapping(
                simulations["detection_probabilities"], "detection_probabilities"
            ),
        )
        posterior_results = fuse_evidence(hypotheses, evidence_components)
        evidence_summary = tuple(
            _summarize_component(component) for component in evidence_components
        )
        posterior_summary = _summarize_posterior(posterior_results)
        hashes = {
            "evidence": sha256_payload(evidence_summary),
            "posterior": sha256_payload(posterior_summary),
        }
        hashes["artifact"] = sha256_payload(
            {
                "case_id": metadata["case_id"],
                "schema_version": metadata["schema_version"],
                "evidence_components": evidence_summary,
                "posteriors": posterior_summary,
                "hashes": hashes,
            }
        )

        return ReplayArtifact(
            case_id=str(metadata["case_id"]),
            schema_version=str(metadata["schema_version"]),
            evidence_components=evidence_summary,
            posteriors=posterior_summary,
            hashes=hashes,
        )


def compare_artifacts(
    expected: ReplayArtifact,
    actual: ReplayArtifact,
) -> tuple[str, ...]:
    """Return mismatch labels for two replay artifacts."""
    mismatches: list[str] = []
    if expected.case_id != actual.case_id:
        mismatches.append("case_id")
    if expected.schema_version != actual.schema_version:
        mismatches.append("schema_version")
    if expected.evidence_components != actual.evidence_components:
        mismatches.append("evidence_components")
    if expected.posteriors != actual.posteriors:
        mismatches.append("posteriors")
    if dict(expected.hashes) != dict(actual.hashes):
        mismatches.append("hashes")
    return tuple(mismatches)
