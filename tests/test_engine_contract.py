"""Tests for the L10.1 engine interface contract."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.engine.contract import (
    ChannelRequest,
    ConstraintConfig,
    EngineError,
    EngineErrorCode,
    EngineRequest,
    EngineResponse,
    EngineStatus,
    FusionConfig,
    PosteriorResult,
    TraceOperation,
    TraceStep,
)


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
        admissibility_threshold=0.01,
    )


def test_valid_request_is_frozen(
    fusion_config: FusionConfig,
    constraint_config: ConstraintConfig,
) -> None:
    request = EngineRequest(
        engine_version="10.1.0",
        contract_version="v1",
        request_id="12345678-1234-5678-1234-567812345678",
        timestamp="2026-07-06T12:00:00+10:00",
        channels=(
            ChannelRequest(
                channel_id="satcom",
                adapter_version="9.2.0",
                inline_payload_json='{"observed_bto": 12500.0}',
            ),
        ),
        fusion_config=fusion_config,
        constraint_config=constraint_config,
    )

    with pytest.raises(FrozenInstanceError):
        request.engine_version = "10.1.1"


def test_channel_requires_exactly_one_payload_source() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        ChannelRequest(channel_id="satcom", adapter_version="9.2.0")


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
            channels=(
                ChannelRequest(
                    channel_id="satcom",
                    adapter_version="9.2.0",
                    payload_ref="fixture://satcom",
                ),
            ),
            fusion_config=fusion_config,
            constraint_config=constraint_config,
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
        trace=(
            TraceStep(
                step_id="step-1",
                operation=TraceOperation.FUSION_STEP,
                inputs_ref="sha256:input",
                outputs_ref="sha256:output",
                duration_ms=1.5,
            ),
        ),
        replay_hash="a" * 64,
    )

    assert response.posterior_distribution[0].probability == 0.75


def test_failure_response_requires_typed_error() -> None:
    error = EngineError(
        code=EngineErrorCode.INVALID_SCHEMA,
        stage="ingest",
        diagnostic_payload_json='{"field": "channels"}',
        recoverable=True,
    )
    response = EngineResponse(
        request_id="12345678-1234-5678-1234-567812345678",
        engine_version="10.1.0",
        contract_version="v1",
        status=EngineStatus.FAILURE,
        posterior_distribution=(),
        argmax_hypothesis_id=None,
        trace=(),
        replay_hash="b" * 64,
        error=error,
    )

    assert response.error is error


def test_invalid_contract_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="semantic version"):
        ChannelRequest(
            channel_id="satcom",
            adapter_version="L9.2",
            payload_ref="fixture://satcom",
        )

    with pytest.raises(ValueError, match="probability_ceiling"):
        ConstraintConfig(probability_ceiling=1.0, likelihood_floor=1e-12)
