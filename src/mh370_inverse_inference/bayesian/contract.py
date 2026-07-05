"""Immutable Bayesian evidence fusion contract with log-space normalization."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import exp, isfinite, isinf, isnan, log


class EvidenceType(StrEnum):
    """Supported evidence contribution categories."""

    BTO = "bto"
    BFO = "bfo"
    DEBRIS_RECOVERY = "debris_recovery"
    NEGATIVE_SEARCH = "negative_search"
    TRAJECTORY_CONSISTENCY = "trajectory_consistency"


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One candidate hypothesis with a linear-space prior weight."""

    hypothesis_id: str
    prior_weight: float

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id must be non-empty")
        if not isfinite(self.prior_weight):
            raise ValueError("prior weight must be finite")
        if self.prior_weight < 0.0:
            raise ValueError("prior weight must be non-negative")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One log-likelihood contribution for a target hypothesis."""

    hypothesis_id: str
    log_likelihood: float

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id must be non-empty")
        if isnan(self.log_likelihood):
            raise ValueError("log_likelihood cannot be NaN")
        if not isfinite(self.log_likelihood) and not (
            isinf(self.log_likelihood) and self.log_likelihood < 0.0
        ):
            raise ValueError("log_likelihood must be finite or negative infinity")


@dataclass(frozen=True, slots=True)
class EvidenceComponent:
    """A named evidence component with provenance and typed records."""

    evidence_type: EvidenceType
    source_id: str
    records: tuple[EvidenceRecord, ...]

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be non-empty")
        if not self.records:
            raise ValueError("evidence component records cannot be empty")


@dataclass(frozen=True, slots=True)
class EvidenceContribution:
    """Auditable contribution retained in a posterior entry."""

    evidence_type: EvidenceType
    source_id: str
    log_likelihood: float


@dataclass(frozen=True, slots=True)
class PosteriorEntry:
    """Fully normalized posterior state for one hypothesis."""

    hypothesis_id: str
    prior_weight: float
    joint_log_score: float
    posterior_probability: float
    contributions: tuple[EvidenceContribution, ...]


def log_sum_exp(scores: Sequence[float]) -> float:
    """Compute stable log-sum-exp while ignoring negative infinity scores."""
    finite_scores = [score for score in scores if isfinite(score)]
    if not finite_scores:
        return -float("inf")
    max_score = max(finite_scores)
    return max_score + log(sum(exp(score - max_score) for score in finite_scores))


def fuse_evidence(
    hypotheses: Sequence[Hypothesis],
    evidence_components: Sequence[EvidenceComponent],
) -> tuple[PosteriorEntry, ...]:
    """Fuse independent evidence components into normalized posterior weights."""
    if not hypotheses:
        raise ValueError("hypotheses cannot be empty")

    hypothesis_ids = tuple(hypothesis.hypothesis_id for hypothesis in hypotheses)
    if len(set(hypothesis_ids)) != len(hypothesis_ids):
        raise ValueError("hypothesis identifiers must be unique")

    joint_scores: dict[str, float] = {}
    contribution_map: dict[str, list[EvidenceContribution]] = {}
    prior_map: dict[str, float] = {}

    for hypothesis in hypotheses:
        prior_map[hypothesis.hypothesis_id] = hypothesis.prior_weight
        joint_scores[hypothesis.hypothesis_id] = (
            log(hypothesis.prior_weight)
            if hypothesis.prior_weight > 0.0
            else -float("inf")
        )
        contribution_map[hypothesis.hypothesis_id] = []

    for component in evidence_components:
        seen: set[str] = set()
        for record in component.records:
            if record.hypothesis_id not in joint_scores:
                raise ValueError(
                    "evidence refers to unknown hypothesis "
                    f"{record.hypothesis_id!r} from source {component.source_id!r}"
                )
            if record.hypothesis_id in seen:
                raise ValueError(
                    "duplicate evidence record for hypothesis "
                    f"{record.hypothesis_id!r} in source {component.source_id!r}"
                )
            seen.add(record.hypothesis_id)
            joint_scores[record.hypothesis_id] += record.log_likelihood
            contribution_map[record.hypothesis_id].append(
                EvidenceContribution(
                    evidence_type=component.evidence_type,
                    source_id=component.source_id,
                    log_likelihood=record.log_likelihood,
                )
            )

    normalizer = log_sum_exp(tuple(joint_scores.values()))
    if normalizer == -float("inf"):
        raise ValueError("all hypotheses have zero posterior support")

    return tuple(
        PosteriorEntry(
            hypothesis_id=hypothesis.hypothesis_id,
            prior_weight=prior_map[hypothesis.hypothesis_id],
            joint_log_score=joint_scores[hypothesis.hypothesis_id],
            posterior_probability=(
                0.0
                if joint_scores[hypothesis.hypothesis_id] == -float("inf")
                else exp(joint_scores[hypothesis.hypothesis_id] - normalizer)
            ),
            contributions=tuple(contribution_map[hypothesis.hypothesis_id]),
        )
        for hypothesis in hypotheses
    )
