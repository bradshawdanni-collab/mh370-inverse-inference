"""Stateless evidence orchestration for Bayesian fusion inputs."""

from collections.abc import Mapping
from dataclasses import dataclass

from mh370_inverse_inference.bayesian.contract import EvidenceComponent
from mh370_inverse_inference.bayesian.negative_search_adapter import (
    NegativeSearchAdapter,
)
from mh370_inverse_inference.bayesian.satcom_adapter import SatcomLikelihoodAdapter
from mh370_inverse_inference.bayesian.trajectory_adapter import (
    TrajectoryConsistencyAdapter,
)


@dataclass(frozen=True, slots=True)
class EvidenceOrchestrator:
    """Coordinate independent evidence adapters without runtime state."""

    satcom_adapter: SatcomLikelihoodAdapter
    trajectory_adapter: TrajectoryConsistencyAdapter
    negative_search_adapter: NegativeSearchAdapter | None = None

    def generate_evidence_stream(
        self,
        *,
        observed_bto: float,
        observed_bfo: float,
        simulated_bto: Mapping[str, float],
        simulated_bfo: Mapping[str, float],
        trajectory_residuals: Mapping[str, float],
        detection_probabilities: Mapping[str, float] | None = None,
    ) -> tuple[EvidenceComponent, ...]:
        """Return an ordered three- or four-channel evidence stream."""
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

        components = [bto_component, bfo_component, trajectory_component]
        if detection_probabilities is not None:
            if self.negative_search_adapter is None:
                raise ValueError(
                    "cannot evaluate negative search metrics without an injected "
                    "NegativeSearchAdapter"
                )
            components.append(
                self.negative_search_adapter.evaluate_negative_search(
                    source_id="ORCHESTRATED-NEGATIVE-SEARCH",
                    detection_probabilities=detection_probabilities,
                )
            )

        return tuple(components)
