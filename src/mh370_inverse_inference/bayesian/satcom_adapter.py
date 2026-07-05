"""Gaussian SATCOM likelihood adapters for the L9.1 Bayesian contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite, log, pi, sqrt

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    EvidenceRecord,
    EvidenceType,
)


@dataclass(frozen=True, slots=True)
class SatcomLikelihoodAdapter:
    """Convert abstract BTO and BFO residuals into frozen evidence components."""

    sigma_bto: float
    sigma_bfo: float

    def __post_init__(self) -> None:
        for name, value in (
            ("sigma_bto", self.sigma_bto),
            ("sigma_bfo", self.sigma_bfo),
        ):
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and strictly positive")

    def evaluate_bto_component(
        self,
        *,
        source_id: str,
        observed_bto: float,
        hypothesis_simulations: Mapping[str, float],
    ) -> EvidenceComponent:
        """Build one BTO evidence component from abstract scalar simulations."""
        return self._evaluate_component(
            evidence_type=EvidenceType.BTO,
            source_id=source_id,
            observed_value=observed_bto,
            hypothesis_simulations=hypothesis_simulations,
            sigma=self.sigma_bto,
        )

    def evaluate_bfo_component(
        self,
        *,
        source_id: str,
        observed_bfo: float,
        hypothesis_simulations: Mapping[str, float],
    ) -> EvidenceComponent:
        """Build one BFO evidence component from abstract scalar simulations."""
        return self._evaluate_component(
            evidence_type=EvidenceType.BFO,
            source_id=source_id,
            observed_value=observed_bfo,
            hypothesis_simulations=hypothesis_simulations,
            sigma=self.sigma_bfo,
        )

    @staticmethod
    def _evaluate_component(
        *,
        evidence_type: EvidenceType,
        source_id: str,
        observed_value: float,
        hypothesis_simulations: Mapping[str, float],
        sigma: float,
    ) -> EvidenceComponent:
        if not source_id:
            raise ValueError("source_id must be non-empty")
        if not isfinite(observed_value):
            raise ValueError("observed SATCOM value must be finite")
        if not hypothesis_simulations:
            raise ValueError("hypothesis simulations cannot be empty")

        normalization = -log(sigma * sqrt(2.0 * pi))
        records: list[EvidenceRecord] = []
        for hypothesis_id in sorted(hypothesis_simulations):
            if not hypothesis_id:
                raise ValueError("hypothesis identifiers must be non-empty")
            simulated_value = hypothesis_simulations[hypothesis_id]
            if not isfinite(simulated_value):
                raise ValueError(
                    f"simulated SATCOM value for {hypothesis_id!r} must be finite"
                )
            standardized_residual = (simulated_value - observed_value) / sigma
            records.append(
                EvidenceRecord(
                    hypothesis_id=hypothesis_id,
                    log_likelihood=normalization - 0.5 * standardized_residual**2,
                )
            )

        return EvidenceComponent(
            evidence_type=evidence_type,
            source_id=source_id,
            records=tuple(records),
        )
