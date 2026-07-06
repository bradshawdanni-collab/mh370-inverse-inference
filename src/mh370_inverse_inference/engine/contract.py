"""Immutable interface contract for deterministic inference engine requests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
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


class FailureDeterminism(StrEnum):
    DETERMINISTIC = "deterministic"
    NON_DETERMINISTIC = "non_deterministic"


class NegativeEvidenceModel(StrEnum):
    HARD_EXCLUSION = "hard_exclusion"
    LIKELIHOOD_PENALTY = "likelihood_penalty"


class NumericPrecision(StrEnum):
    FLOAT64 = "float64"
    DECIMAL128 = "decimal128"


class RoundingMode(StrEnum):
    HALF_EVEN = "half_even"


class CanonicalJsonPolicy(StrEnum):
    SORTED_UTF8_NO_INSIGNIFICANT_WHITESPACE = (
        "sorted_utf8_no_insignificant_whitespace"
    )


class ExecutionStage(StrEnum):
    ADAPTER_NORMALIZATION = "adapter_normalization"
    LIKELIHOOD_EVALUATION = "likelihood_evaluation"
    FUSION = "fusion"
    CONSTRAINT_APPLICATION = "constraint_application"
    NORMALIZATION = "normalization"


CANONICAL_EXECUTION_ORDER = (
    ExecutionStage.ADAPTER_NORMALIZATION,
    ExecutionStage.LIKELIHOOD_EVALUATION,
    ExecutionStage.FUSION,
    ExecutionStage.CONSTRAINT_APPLICATION,
    ExecutionStage.NORMALIZATION,
)


def _validate_semver(value: str, name: str) -> None:
    if not _SEMVER.fullmatch(value):
        raise ValueError(f"{name} must be semantic version MAJOR.MINOR.PATCH")


def _validate_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be non-empty")


def _validate_sha256(value: str, name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


@dataclass(frozen=True, slots=True)
class DeterminismSpec:
    numeric_precision: NumericPrecision = NumericPrecision.FLOAT64
    rounding_mode: RoundingMode = RoundingMode.HALF_EVEN
    canonical_json: CanonicalJsonPolicy = (
        CanonicalJsonPolicy.SORTED_UTF8_NO_INSIGNIFICANT_WHITESPACE
    )
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.seed is not None and self.seed < 0:
            raise ValueError("seed must be non-negative when supplied")


@dataclass(frozen=True, slots=True)
class ChannelRequest:
    channel_id: str
    adapter_version: str
    schema_hash: str
    transform_hash: str
    payload_ref: str | None = None
    inline_payload_json: str | None = None
    confidence_prior: float | None = None

    def __post_init__(self) -> None:
        _validate_non_empty(self.channel_id, "channel_id")
        _validate_semver(self.adapter_version, "adapter_version")
        _validate_sha256(self.schema_hash, "schema_hash")
        _validate_sha256(self.transform_hash, "transform_hash")
        if (self.payload_ref is None) == (self.inline_payload_json is None):
            raise ValueError("exactly one payload source is required")
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
    negative_evidence_model: NegativeEvidenceModel = (
        NegativeEvidenceModel.LIKELIHOOD_PENALTY
    )
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
    determinism_spec: DeterminismSpec = field(default_factory=DeterminismSpec)
    execution_order: tuple[ExecutionStage, ...] = CANONICAL_EXECUTION_ORDER
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    trace_level: TraceLevel = TraceLevel.STANDARD

    def __post_init__(self) -> None:
        _validate_semver(self.engine_version, "engine_version")
        _validate_non_empty(self.contract_version, "contract_version")
        UUID(self.request_id)
        timestamp = self.timestamp.replace("Z", "+00:00")
        parsed_timestamp = datetime.fromisoformat(timestamp)
        if parsed_timestamp.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        if not self.channels:
            raise ValueError("channels cannot be empty")
        channel_ids = tuple(channel.channel_id for channel in self.channels)
        if len(channel_ids) != len(set(channel_ids)):
            raise ValueError("channel_id values must be unique")
        if self.execution_order != CANONICAL_EXECUTION_ORDER:
            raise ValueError("execution_order must match the L10.1 canonical order")


@dataclass(frozen=True, slots=True)
class TraceStep:
    step_id: str
    operation: TraceOperation
    inputs_ref: str
    outputs_ref: str
    input_hash: str
    output_hash: str
    op_signature_hash: str
    duration_ms: float
    deterministic_seed: int | None = None

    def __post_init__(self) -> None:
        _validate_non_empty(self.step_id, "step_id")
        _validate_non_empty(self.inputs_ref, "inputs_ref")
        _validate_non_empty(self.outputs_ref, "outputs_ref")
        _validate_sha256(self.input_hash, "input_hash")
        _validate_sha256(self.output_hash, "output_hash")
        _validate_sha256(self.op_signature_hash, "op_signature_hash")
        if not isfinite(self.duration_ms) or self.duration_ms < 0.0:
            raise ValueError("duration_ms must be finite and non-negative")
        if self.deterministic_seed is not None and self.deterministic_seed < 0:
            raise ValueError("deterministic_seed must be non-negative when supplied")


@dataclass(frozen=True, slots=True)
class EngineError:
    code: EngineErrorCode
    stage: str
    diagnostic_payload_json: str
    recoverable: bool
    failure_determinism: FailureDeterminism

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
class ConstraintEffects:
    excluded_mass: float = 0.0
    penalized_mass: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("excluded_mass", self.excluded_mass),
            ("penalized_mass", self.penalized_mass),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and within [0, 1]")


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
    normalization_error: float
    pre_normalization_mass: float
    constraint_effects: ConstraintEffects = field(default_factory=ConstraintEffects)
    error: EngineError | None = None

    def __post_init__(self) -> None:
        UUID(self.request_id)
        _validate_semver(self.engine_version, "engine_version")
        _validate_non_empty(self.contract_version, "contract_version")
        _validate_sha256(self.replay_hash, "replay_hash")
        if (
            not isfinite(self.normalization_error)
            or self.normalization_error < 0.0
        ):
            raise ValueError("normalization_error must be finite and non-negative")
        if (
            not isfinite(self.pre_normalization_mass)
            or self.pre_normalization_mass < 0.0
        ):
            raise ValueError("pre_normalization_mass must be finite and non-negative")
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
            if abs(total - 1.0) > self.normalization_error + 1e-15:
                raise ValueError("normalization_error must bound posterior sum error")
            if self.argmax_hypothesis_id is None:
                raise ValueError(
                    "successful posterior responses require argmax_hypothesis_id"
                )
            ids = {item.hypothesis_id for item in self.posterior_distribution}
            if self.argmax_hypothesis_id not in ids:
                raise ValueError(
                    "argmax_hypothesis_id must reference a posterior entry"
                )
        step_ids = tuple(step.step_id for step in self.trace)
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("trace step identifiers must be unique")
