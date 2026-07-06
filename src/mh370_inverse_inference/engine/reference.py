"""Deterministic reference engine for the frozen L9 Bayesian fixture."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    Hypothesis,
    PosteriorEntry,
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
from mh370_inverse_inference.engine.contract import (
    EngineResponse,
    EngineStatus,
    PosteriorResult,
    TraceOperation,
    TraceStep,
)
from mh370_inverse_inference.engine.hashing import compose_replay_hash, sha256_payload
from mh370_inverse_inference.engine.trace import TraceMetricRecord
from mh370_inverse_inference.engine.trace_builder import TraceBuilder

ENGINE_VERSION = "10.5.0"
CONTRACT_VERSION = "v1"
REQUEST_ID = "12345678-1234-5678-1234-567812345678"
OP_SIGNATURE_HASH = sha256_payload({"engine": "reference", "version": ENGINE_VERSION})


def load_fixture(path: Path) -> dict[str, Any]:
    """Load one frozen fixture JSON object."""
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    if not isinstance(loaded, dict):
        raise ValueError("reference engine fixture must contain a JSON object")
    return loaded


def _float_mapping(value: object, name: str) -> Mapping[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return {str(key): float(raw_value) for key, raw_value in value.items()}


def _trace_step(
    *,
    stage_id: str,
    stage_index: int,
    operation: TraceOperation,
    stage_input: object,
    stage_output: object,
    record_count: int | None = None,
    hypothesis_count: int | None = None,
    normalization_error: float | None = None,
    pre_normalization_mass: float | None = None,
) -> tuple[TraceMetricRecord, TraceStep]:
    input_hash = sha256_payload(stage_input)
    output_hash = sha256_payload(stage_output)
    record = TraceMetricRecord.from_parts(
        stage_id=stage_id,
        stage_index=stage_index,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=OP_SIGNATURE_HASH,
        duration_ms=0.0,
        record_count=record_count,
        hypothesis_count=hypothesis_count,
        normalization_error=normalization_error,
        pre_normalization_mass=pre_normalization_mass,
    )
    step = TraceStep(
        step_id=stage_id,
        operation=operation,
        inputs_ref=f"sha256:{input_hash}",
        outputs_ref=f"sha256:{output_hash}",
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=OP_SIGNATURE_HASH,
        duration_ms=0.0,
    )
    return record, step


def _component_payloads(
    components: Sequence[EvidenceComponent],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "evidence_type": component.evidence_type.value,
            "source_id": component.source_id,
            "records": tuple(
                {
                    "hypothesis_id": record.hypothesis_id,
                    "log_likelihood": record.log_likelihood,
                }
                for record in component.records
            ),
        }
        for component in components
    )


def _posterior_payloads(
    results: Sequence[PosteriorEntry],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "hypothesis_id": result.hypothesis_id,
            "prior_weight": result.prior_weight,
            "joint_log_score": result.joint_log_score,
            "posterior_probability": result.posterior_probability,
        }
        for result in results
    )


def run_reference_engine(fixture_path: Path) -> EngineResponse:
    """Run the single-threaded reference engine over one frozen fixture."""
    fixture = load_fixture(fixture_path)
    builder = TraceBuilder()
    trace_steps: list[TraceStep] = []

    stage_input = {"fixture_path": str(fixture_path)}
    stage_output = fixture
    record, step = _trace_step(
        stage_id="adapter_normalization",
        stage_index=0,
        operation=TraceOperation.ADAPTER_TRANSFORM,
        stage_input=stage_input,
        stage_output=stage_output,
    )
    builder.add(record)
    trace_steps.append(step)

    hypotheses = tuple(
        Hypothesis(
            hypothesis_id=str(item["hypothesis_id"]),
            prior_weight=float(item["prior_weight"]),
        )
        for item in fixture["hypotheses"]
    )
    parameters = fixture["parameters"]
    observations = fixture["observations"]
    simulations = fixture["simulations"]
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
        simulated_bto=_float_mapping(
            simulations["simulated_bto"],
            "simulated_bto",
        ),
        simulated_bfo=_float_mapping(
            simulations["simulated_bfo"],
            "simulated_bfo",
        ),
        trajectory_residuals=_float_mapping(
            simulations["trajectory_residuals"],
            "trajectory_residuals",
        ),
        detection_probabilities=_float_mapping(
            simulations["detection_probabilities"],
            "detection_probabilities",
        ),
    )
    evidence_payloads = _component_payloads(evidence_components)
    record, step = _trace_step(
        stage_id="likelihood_evaluation",
        stage_index=1,
        operation=TraceOperation.LIKELIHOOD_EVAL,
        stage_input=stage_output,
        stage_output=evidence_payloads,
        record_count=sum(len(component.records) for component in evidence_components),
        hypothesis_count=len(hypotheses),
    )
    builder.add(record)
    trace_steps.append(step)

    posterior_entries = fuse_evidence(hypotheses, evidence_components)
    posterior_payloads = _posterior_payloads(posterior_entries)
    pre_normalization_mass = sum(
        entry.posterior_probability for entry in posterior_entries
    )
    normalization_error = abs(1.0 - pre_normalization_mass)
    record, step = _trace_step(
        stage_id="fusion",
        stage_index=2,
        operation=TraceOperation.FUSION_STEP,
        stage_input=evidence_payloads,
        stage_output=posterior_payloads,
        record_count=len(posterior_entries),
        hypothesis_count=len(hypotheses),
        normalization_error=normalization_error,
        pre_normalization_mass=pre_normalization_mass,
    )
    builder.add(record)
    trace_steps.append(step)

    constraint_output = {
        "excluded_mass": 0.0,
        "penalized_mass": 0.0,
        "model": "likelihood_penalty",
    }
    record, step = _trace_step(
        stage_id="constraint_application",
        stage_index=3,
        operation=TraceOperation.CONSTRAINT_PRUNE,
        stage_input=posterior_payloads,
        stage_output=constraint_output,
        hypothesis_count=len(hypotheses),
    )
    builder.add(record)
    trace_steps.append(step)

    distribution = tuple(
        PosteriorResult(
            hypothesis_id=entry.hypothesis_id,
            probability=entry.posterior_probability,
        )
        for entry in posterior_entries
    )
    argmax = max(posterior_entries, key=lambda entry: entry.posterior_probability)
    response_payload = {
        "posterior_distribution": tuple(
            {
                "hypothesis_id": result.hypothesis_id,
                "probability": result.probability,
            }
            for result in distribution
        ),
        "argmax_hypothesis_id": argmax.hypothesis_id,
        "normalization_error": normalization_error,
        "pre_normalization_mass": pre_normalization_mass,
    }
    record, step = _trace_step(
        stage_id="normalization",
        stage_index=4,
        operation=TraceOperation.FUSION_STEP,
        stage_input=posterior_payloads,
        stage_output=response_payload,
        record_count=len(distribution),
        hypothesis_count=len(hypotheses),
        normalization_error=normalization_error,
        pre_normalization_mass=pre_normalization_mass,
    )
    builder.add(record)
    trace_steps.append(step)

    execution_trace = builder.finish()
    replay_hash = compose_replay_hash(
        step_hashes=tuple(record.trace_hash for record in execution_trace.records),
        final_posterior_hash=sha256_payload(response_payload),
    )
    return EngineResponse(
        request_id=REQUEST_ID,
        engine_version=ENGINE_VERSION,
        contract_version=CONTRACT_VERSION,
        status=EngineStatus.SUCCESS,
        posterior_distribution=distribution,
        argmax_hypothesis_id=argmax.hypothesis_id,
        trace=tuple(trace_steps),
        replay_hash=replay_hash,
        normalization_error=normalization_error,
        pre_normalization_mass=pre_normalization_mass,
    )
