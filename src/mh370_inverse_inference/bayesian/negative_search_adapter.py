"""Negative-search likelihood adapter for the Bayesian evidence contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite, log

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    EvidenceRecord,
    EvidenceType,
)


@dataclass(frozen=True, slots=True)
class NegativeSearchAdapter:
    """Convert detection probabilities into finite non-detection penalties."""

    probability_ceiling: float = 1.0 - 1e-12
    likelihood_floor: float = 1e-12

    def __post_init__(self) -> None:
        if not isfinite(self.probability_ceiling) or not (
            0.0 < self.probability_ceiling < 1.0
        ):
            raise ValueError("probability_ceiling must be finite and within (0, 1)")
        if not isfinite(self.likelihood_floor) or not (
            0.0 < self.likelihood_floor <= 1.0
        ):
            raise ValueError("likelihood_floor must be finite and within (0, 1]")

    def evaluate_negative_search(
        self,
        *,
        source_id: str,
        detection_probabilities: Mapping[str, float],
    ) -> EvidenceComponent:
        """Build deterministic negative-search evidence records."""
        if not source_id:
            raise ValueError("source_id must be non-empty")
        if not detection_probabilities:
            raise ValueError("detection probabilities cannot be empty")

        records: list[EvidenceRecord] = []
        for hypothesis_id in sorted(detection_probabilities):
            if not hypothesis_id:
                raise ValueError("hypothesis identifiers must be non-empty")
            probability = detection_probabilities[hypothesis_id]
            if not isfinite(probability):
                raise ValueError(
                    f"detection probability for {hypothesis_id!r} must be finite"
                )
            if not 0.0 <= probability <= 1.0:
                raise ValueError(
                    f"detection probability for {hypothesis_id!r} must be within [0, 1]"
                )

            bounded_probability = min(probability, self.probability_ceiling)
            non_detection_likelihood = max(
                1.0 - bounded_probability,
                self.likelihood_floor,
            )
            records.append(
                EvidenceRecord(
                    hypothesis_id=hypothesis_id,
                    log_likelihood=log(non_detection_likelihood),
                )
            )

        return EvidenceComponent(
            evidence_type=EvidenceType.NEGATIVE_SEARCH,
            source_id=source_id,
            records=tuple(records),
        )
