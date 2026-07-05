"""Deterministic candidate admissibility checks over residual records."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class ConstraintTolerance:
    """Explicit residual tolerances for candidate evaluation."""

    bto_slant_range_m: float | None = None
    bfo_hz: float | None = None
    reachability_m: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("bto_slant_range_m", self.bto_slant_range_m),
            ("bfo_hz", self.bfo_hz),
            ("reachability_m", self.reachability_m),
        ):
            if value is None:
                continue
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} tolerance must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class CandidateResiduals:
    """Individual residuals associated with one candidate state."""

    candidate_id: str
    bto_slant_range_m: float | None = None
    bfo_hz: float | None = None
    reachability_m: float | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        for name, value in (
            ("bto_slant_range_m", self.bto_slant_range_m),
            ("bfo_hz", self.bfo_hz),
            ("reachability_m", self.reachability_m),
        ):
            if value is not None and not isfinite(value):
                raise ValueError(f"{name} residual must be finite when provided")


@dataclass(frozen=True, slots=True)
class ConstraintDecision:
    """Pass/fail state for one constraint."""

    enabled: bool
    passed: bool
    residual: float | None
    tolerance: float | None


@dataclass(frozen=True, slots=True)
class CandidateAdmissibility:
    """Complete deterministic decision record for one candidate."""

    candidate_id: str
    bto: ConstraintDecision
    bfo: ConstraintDecision
    reachability: ConstraintDecision

    @property
    def admissible(self) -> bool:
        """Return True only when every enabled constraint passes."""
        return all(
            decision.passed
            for decision in (self.bto, self.bfo, self.reachability)
            if decision.enabled
        )


def _evaluate_constraint(
    *, residual: float | None, tolerance: float | None
) -> ConstraintDecision:
    enabled = tolerance is not None
    if not enabled:
        return ConstraintDecision(
            enabled=False,
            passed=False,
            residual=residual,
            tolerance=None,
        )
    if residual is None:
        return ConstraintDecision(
            enabled=True,
            passed=False,
            residual=None,
            tolerance=tolerance,
        )
    return ConstraintDecision(
        enabled=True,
        passed=abs(residual) <= tolerance,
        residual=residual,
        tolerance=tolerance,
    )


def evaluate_candidate_admissibility(
    residuals: CandidateResiduals,
    tolerances: ConstraintTolerance,
) -> CandidateAdmissibility:
    """Evaluate one candidate against explicitly enabled tolerances."""
    return CandidateAdmissibility(
        candidate_id=residuals.candidate_id,
        bto=_evaluate_constraint(
            residual=residuals.bto_slant_range_m,
            tolerance=tolerances.bto_slant_range_m,
        ),
        bfo=_evaluate_constraint(
            residual=residuals.bfo_hz,
            tolerance=tolerances.bfo_hz,
        ),
        reachability=_evaluate_constraint(
            residual=residuals.reachability_m,
            tolerance=tolerances.reachability_m,
        ),
    )


def evaluate_candidate_batch(
    residuals: tuple[CandidateResiduals, ...],
    tolerances: ConstraintTolerance,
) -> tuple[CandidateAdmissibility, ...]:
    """Evaluate candidates in input order."""
    return tuple(
        evaluate_candidate_admissibility(candidate, tolerances)
        for candidate in residuals
    )
