"""Evidence records for probabilistic trajectory inference."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class GaussianEvidence:
    """One residual observation with a caller-supplied Gaussian scale."""

    evidence_id: str
    residual: float
    sigma: float

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id must be non-empty")
        if not isfinite(self.residual):
            raise ValueError("residual must be finite")
        if not isfinite(self.sigma) or self.sigma <= 0.0:
            raise ValueError("sigma must be finite and positive")


@dataclass(frozen=True, slots=True)
class TrajectoryEvidence:
    """Evidence terms associated with one trajectory hypothesis."""

    trajectory_id: str
    terms: tuple[GaussianEvidence, ...]

    def __post_init__(self) -> None:
        if not self.trajectory_id:
            raise ValueError("trajectory_id must be non-empty")
        if not self.terms:
            raise ValueError("at least one evidence term is required")
        evidence_ids = tuple(term.evidence_id for term in self.terms)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence_id values must be unique per trajectory")
