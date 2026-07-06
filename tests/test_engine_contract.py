"""Tests for the L10.1 engine interface contract."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.engine.contract import (
    ChannelRequest,
    ConstraintConfig,
    ConstraintEffects,
    DeterminismSpec,
    EngineError,
    EngineErrorCode,
    EngineRequest,
    EngineResponse,
    EngineStatus,
    ExecutionStage,
    FailureDeterminism,
    FusionConfig,
    NegativeEvidenceModel,
    PosteriorResult,
    TraceOperation,
    TraceStep,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


@pytest.fixture
def fusion_config() -> FusionConfig:
    return FusionConfig(
        contract_version="v1",
        prior_policy="fixture",
        independence_assumption="independent_channels",
    )


@pytest.fixture
def constraint_config() -> ConstraintConfig:
    return ConstraintConfig(
        probability_ceiling=0.9999,
        likelihood_floor=1e-12,
        negative_evidence_model=NegativeEvidenceModel.LIKELIHOOD_PENALTY,
        admissibility_threshold=0.01,
    )


def channel_request(channel_id: str = "satcom") -> ChannelRequest:
    return ChannelRequest(
        channel_id=channel_id,
        adapter_version="9.2.0",
        schema_hash=HASH_A,
        transform_hash=HASH_B,
        inline_payload_json='{"observed_bto": 12500.0}',
    )


def trace_step(step_id: str = "step-1") -> TraceStep:
    return TraceStep(
        step_id=step_id,
        operation=TraceOperation.FUSION_STEP,
        inputs_ref="sha256:input",
        outputs_ref="sha256:output",
        input_hash=HASH_A,
        output_hash=HASH_B,
        op_signature_hash=HASH_C,
        duration_ms=1.5,
    )


def test_valid_request_is_frozen_and_canonical(
    fusion_config: FusionConfig,
    constraint_config: ConstraintConfig,
) -> None:
    request = EngineRequest(
        engine_version="10.1.0",
        contract_version="v1",
        request_id="12345678-1234-5678-1234-567812345678",
        timestamp="2026-07-06T12:00:00+10:00",
        channels=(channel_request(),),
        fusion_config=fusion_config,
        constraint_config=constraint_config,
        determinism_spec=DeterminismSpec(seed=42),
    )

    assert request.execution_order == (
        ExecutionStage.ADAPTER_NORMALIZATION,
        ExecutionStage.LIKELIHOOD_EVALUATION,
        ExecutionStage.FUSION,
        ExecutionStage.CONSTRAINT_APPLICATION,
        ExecutionStage.NORMALIZATION,
    )
    with pytest.raises(FrozenInstanceError):
        request.engine_version = "10.1.1"


def test_channel_requires_exactly_one_payload_source() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        ChannelRequest(
            channel_id="satcom",
            adapter_version="9.2.0",
            schema_hash=HASH_A,
            transform_hash=HASH_B,
        )


def test_channel_requires_schema_and_transform_hashes() -> None:
    with pytest.raises(ValueError, match="schema_hash"):
        ChannelRequest(
            channel_id="satcom",
            adapter_version="9.2.0",
            schema_hash="not-a-hash",
            transform_hash=HASH_B,
            payload_ref="fixture://satcom",
        )


def test_request_rejects_naive_timestamp(
    fusion_config: FusionConfig,
    constraint_config: ConstraintConfig,
) -> None:
    with pytest.raises(ValueError, match="timezone"):
        EngineRequest(
            engine_version="10.1.0",
            contract_version="v1",
            request_id="12345678-1234-5678-1234-567812345678",
            timestamp="2026-07-06T12:00:00",
            channels=(channel_request(),),
            fusion_config=fusion_config,
            constraint_config=constraint_config,
        )


def test_request_rejects_noncanonical_execution_order(
    fusion_config: FusionConfig,
    constraint_config: ConstraintConfig,
) -> None:
    with pytest.raises(ValueError, match="canonical order"):
        EngineRequest(
            engine_version="10.1.0",
            contract_version="v1",
            request_id="12345678-1234-5678-1234-567812345678",
            timestamp="2026-07-06T12:00:00Z",
            channels=(channel_request(),),
            fusion_config=fusion_config,
            constraint_config=constraint_config,
            execution_order=(ExecutionStage.FUSION,),
        )


def test_success_response_requires_normalized_posterior() -> None:
    response = EngineResponse(
        request_id="12345678-1234-5678-1234-567812345678",
        engine_version="10.1.0",
        contract_version="v1",
        status=EngineStatus.SUCCESS,
        posterior_distribution=(
            PosteriorResult(hypothesis_id="H-1", probability=0.75),
            PosteriorResult(hypothesis_id="H-2", probability=0.25),
        ),
        argmax_hypothesis_id="H-1",
        trace=(trace_step(),),
        replay_hash=HASH_D,
        normalization_error=0.0,
        pre_normalization_mass=1.0,
        constraint_effects=ConstraintEffects(
            excluded_mass=0.0,
            penalized_mass=0.2,
        ),
    )

    assert response.posterior_distribution[0].probability == 0.75


def test_trace_steps_require_hashable_boundaries() -> None:
    with pytest.raises(ValueError, match="input_hash"):
        TraceStep(
            step_id="step-1",
            operation=TraceOperation.FUSION_STEP,
            inputs_ref="sha256:input",
            outputs_ref="sha256:output",
            input_hash="bad",
            output_hash=HASH_B,
            op_signature_hash=HASH_C,
            duration_ms=1.5,
        )


def test_failure_response_requires_typed_error_with_determinism() -> None:
    error = EngineError(
        code=EngineErrorCode.INVALID_SCHEMA,
        stage="ingest",
        diagnostic_payload_json='{"field": "channels"}',
        recoverable=True,
        failure_determinism=FailureDeterminism.DETERMINISTIC,
    )
    response = EngineResponse(
        request_id="12345678-1234-5678-1234-567812345678",
        engine_version="10.1.0",
        contract_version="v1",
        status=EngineStatus.FAILURE,
        posterior_distribution=(),
        argmax_hypothesis_id=None,
        trace=(),
        replay_hash=HASH_D,
        normalization_error=0.0,
        pre_normalization_mass=0.0,
        error=error,
    )

    assert response.error is error


def test_invalid_contract_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="semantic version"):
        ChannelRequest(
            channel_id="satcom",
            adapter_version="L9.2",
            schema_hash=HASH_A,
            transform_hash=HASH_B,
            payload_ref="fixture://satcom",
        )

    with pytest.raises(ValueError, match="probability_ceiling"):
        ConstraintConfig(probability_ceiling=1.0, likelihood_floor=1e-12)

    with pytest.raises(ValueError, match="seed"):
        DeterminismSpec(seed=-1)
