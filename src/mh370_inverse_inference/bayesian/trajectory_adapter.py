"""Trajectory consistency adapter for the Bayesian evidence contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite, log, pi, sqrt

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    EvidenceRecord,
    EvidenceType,
)


@dataclass(frozen=True, slots=True)
class TrajectoryConsistencyAdapter:
    """Convert scalar trajectory residuals into Gaussian evidence records."""

    sigma_residual: float

    def __post_init__(self) -> None:
        if not isfinite(self.sigma_residual) or self.sigma_residual <= 0.0:
            raise ValueError("sigma_residual must be finite and strictly positive")

    def evaluate_consistency(
        self,
        *,
        source_id: str,
        hypothesis_residuals: Mapping[str, float],
    ) -> EvidenceComponent:
        """Build deterministic trajectory consistency evidence."""
        if not source_id:
            raise ValueError("source_id must be non-empty")
        if not hypothesis_residuals:
            raise ValueError("hypothesis residuals cannot be empty")

        normalization = -log(self.sigma_residual * sqrt(2.0 * pi))
        records: list[EvidenceRecord] = []
        for hypothesis_id in sorted(hypothesis_residuals):
            if not hypothesis_id:
                raise ValueError("hypothesis identifiers must be non-empty")
            residual = hypothesis_residuals[hypothesis_id]
            if not isfinite(residual):
                raise ValueError(
                    f"trajectory residual for {hypothesis_id!r} must be finite"
                )
            standardized_residual = residual / self.sigma_residual
            records.append(
                EvidenceRecord(
                    hypothesis_id=hypothesis_id,
                    log_likelihood=normalization - 0.5 * standardized_residual**2,
                )
            )

        return EvidenceComponent(
            evidence_type=EvidenceType.TRAJECTORY_CONSISTENCY,
            source_id=source_id,
            records=tuple(records),
        )
