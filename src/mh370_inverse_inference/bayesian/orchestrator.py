"""Stateless evidence orchestration for Bayesian fusion inputs."""

from collections.abc import Mapping
from dataclasses import dataclass

from mh370_inverse_inference.bayesian.contract import EvidenceComponent
from mh370_inverse_inference.bayesian.satcom_adapter import SatcomLikelihoodAdapter
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)


@dataclass(frozen=True, slots=True)
class EvidenceOrchestrator:
    """Coordinate independent evidence adapters without runtime state."""

    satcom_adapter: SatcomLikelihoodAdapter
    trajectory_adapter: TrajectoryConsistencyAdapter

    def generate_evidence_stream(
        self,
        *,
        observed_bto: float,
        observed_bfo: float,
        simulated_bto: Mapping[str, float],
        simulated_bfo: Mapping[str, float],
        trajectory_residuals: Mapping[str, float],
    ) -> tuple[EvidenceComponent, ...]:
        """Return ordered BTO, BFO, and trajectory-consistency evidence."""
        bto_component = self.satcom_adapter.evaluate_bto_component(
            source_id="ORCHESTRATED-SATCOM-BTO",
            observed_bto=observed_bto,
            hypothesis_simulations=simulated_bto,
        )
        bfo_component = self.satcom_adapter.evaluate_bfo_component(
            source_id="ORCHESTRATED-SATCOM-BFO",
            observed_bfo=observed_bfo,
            hypothesis_simulations=simulated_bfo,
        )
        trajectory_component = self.trajectory_adapter.evaluate_consistency(
            source_id="ORCHESTRATED-TRAJECTORY-CONSISTENCY",
            hypothesis_residuals=trajectory_residuals,
        )

        return (bto_component, bfo_component, trajectory_component)
