"""Immutable interface contract for deterministic inference engine requests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite
from uuid import UUID

_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ExecutionMode(StrEnum):
    DETERMINISTIC = "deterministic"
    EXPLORATORY = "exploratory"


class TraceLevel(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class EngineStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class TraceOperation(StrEnum):
    ADAPTER_TRANSFORM = "adapter_transform"
    LIKELIHOOD_EVAL = "likelihood_eval"
    FUSION_STEP = "fusion_step"
    CONSTRAINT_PRUNE = "constraint_prune"


class EngineErrorCode(StrEnum):
    INVALID_SCHEMA = "INVALID_SCHEMA"
    ADAPTER_MISMATCH = "ADAPTER_MISMATCH"
    INCONSISTENT_CHANNELS = "INCONSISTENT_CHANNELS"
    NUMERICAL_INSTABILITY = "NUMERICAL_INSTABILITY"
    CONSTRAINT_INFEASIBLE = "CONSTRAINT_INFEASIBLE"


def _validate_semver(value: str, name: str) -> None:
    if not _SEMVER.fullmatch(value):
        raise ValueError(f"{name} must be semantic version MAJOR.MINOR.PATCH")


def _validate_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class ChannelRequest:
    channel_id: str
    adapter_version: str
    payload_ref: str | None = None
    inline_payload_json: str | None = None
    confidence_prior: float | None = None

    def __post_init__(self) -> None:
        _validate_non_empty(self.channel_id, "channel_id")
        _validate_semver(self.adapter_version, "adapter_version")
        if (self.payload_ref is None) == (self.inline_payload_json is None):
            raise ValueError("exactly one of payload_ref or inline_payload_json is required")
        if self.payload_ref is not None:
            _validate_non_empty(self.payload_ref, "payload_ref")
        if self.inline_payload_json is not None:
            parsed = json.loads(self.inline_payload_json)
            if not isinstance(parsed, dict):
                raise ValueError("inline_payload_json must encode a JSON object")
        if self.confidence_prior is not None:
            if not isfinite(self.confidence_prior):
                raise ValueError("confidence_prior must be finite")
            if not 0.0 <= self.confidence_prior <= 1.0:
                raise ValueError("confidence_prior must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class FusionConfig:
    contract_version: str
    prior_policy: str
    independence_assumption: str
    covariance_hints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_non_empty(self.contract_version, "contract_version")
        _validate_non_empty(self.prior_policy, "prior_policy")
        _validate_non_empty(self.independence_assumption, "independence_assumption")


@dataclass(frozen=True, slots=True)
class ConstraintConfig:
    probability_ceiling: float
    likelihood_floor: float
    spatial_bounds_ref: str | None = None
    temporal_bounds_ref: str | None = None
    admissibility_threshold: float | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.probability_ceiling) or not (
            0.0 < self.probability_ceiling < 1.0
        ):
            raise ValueError("probability_ceiling must be finite and within (0, 1)")
        if not isfinite(self.likelihood_floor) or not (
            0.0 < self.likelihood_floor <= 1.0
        ):
            raise ValueError("likelihood_floor must be finite and within (0, 1]")
        if self.admissibility_threshold is not None:
            if not isfinite(self.admissibility_threshold):
                raise ValueError("admissibility_threshold must be finite")
            if not 0.0 <= self.admissibility_threshold <= 1.0:
                raise ValueError("admissibility_threshold must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class EngineRequest:
    engine_version: str
    contract_version: str
    request_id: str
    timestamp: str
    channels: tuple[ChannelRequest, ...]
    fusion_config: FusionConfig
    constraint_config: ConstraintConfig
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    trace_level: TraceLevel = TraceLevel.STANDARD

    def __post_init__(self) -> None:
        _validate_semver(self.engine_version, "engine_version")
        _validate_non_empty(self.contract_version, "contract_version")
        UUID(self.request_id)
        parsed_timestamp = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        if parsed_timestamp.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        if not self.channels:
            raise ValueError("channels cannot be empty")
        channel_ids = tuple(channel.channel_id for channel in self.channels)
        if len(channel_ids) != len(set(channel_ids)):
            raise ValueError("channel_id values must be unique")


@dataclass(frozen=True, slots=True)
class TraceStep:
    step_id: str
    operation: TraceOperation
    inputs_ref: str
    outputs_ref: str
    duration_ms: float
    deterministic_seed: int | None = None

    def __post_init__(self) -> None:
        _validate_non_empty(self.step_id, "step_id")
        _validate_non_empty(self.inputs_ref, "inputs_ref")
        _validate_non_empty(self.outputs_ref, "outputs_ref")
        if not isfinite(self.duration_ms) or self.duration_ms < 0.0:
            raise ValueError("duration_ms must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class EngineError:
    code: EngineErrorCode
    stage: str
    diagnostic_payload_json: str
    recoverable: bool

    def __post_init__(self) -> None:
        _validate_non_empty(self.stage, "stage")
        parsed = json.loads(self.diagnostic_payload_json)
        if not isinstance(parsed, dict):
            raise ValueError("diagnostic_payload_json must encode a JSON object")


@dataclass(frozen=True, slots=True)
class PosteriorResult:
    hypothesis_id: str
    probability: float

    def __post_init__(self) -> None:
        _validate_non_empty(self.hypothesis_id, "hypothesis_id")
        if not isfinite(self.probability) or not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class EngineResponse:
    request_id: str
    engine_version: str
    contract_version: str
    status: EngineStatus
    posterior_distribution: tuple[PosteriorResult, ...]
    argmax_hypothesis_id: str | None
    trace: tuple[TraceStep, ...]
    replay_hash: str
    error: EngineError | None = None

    def __post_init__(self) -> None:
        UUID(self.request_id)
        _validate_semver(self.engine_version, "engine_version")
        _validate_non_empty(self.contract_version, "contract_version")
        if not _SHA256.fullmatch(self.replay_hash):
            raise ValueError("replay_hash must be a lowercase SHA-256 hex digest")
        if self.status is EngineStatus.FAILURE:
            if self.error is None:
                raise ValueError("failure responses require an error")
        elif self.error is not None:
            raise ValueError("non-failure responses cannot include an error")
        if self.status is not EngineStatus.FAILURE and not self.posterior_distribution:
            raise ValueError("non-failure responses require posterior results")
        if self.posterior_distribution:
            total = sum(item.probability for item in self.posterior_distribution)
            if abs(total - 1.0) > 1e-12:
                raise ValueError("posterior probabilities must sum to one")
            if self.argmax_hypothesis_id is None:
                raise ValueError("successful posterior responses require argmax_hypothesis_id")
            ids = {item.hypothesis_id for item in self.posterior_distribution}
            if self.argmax_hypothesis_id not in ids:
                raise ValueError("argmax_hypothesis_id must reference a posterior entry")
        step_ids = tuple(step.step_id for step in self.trace)
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("trace step identifiers must be unique")
