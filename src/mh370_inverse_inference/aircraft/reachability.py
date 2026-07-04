"""Fuel-constrained powered flight and post-exhaustion glide propagation."""

import math

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.propagation import KinematicPropagator
from mh370_inverse_inference.aircraft.state import AircraftState


class ReachabilityEnvelope:
    """Calculate a deterministic L1 terminal state over a bounded duration."""

    GLIDE_DESCENT_RATE = -12.5

    @staticmethod
    def compute_max_range_step(
        state: AircraftState, total_time: float, dt: float = 60.0
    ) -> AircraftState:
        """Propagate powered flight until fuel exhaustion, then glide."""
        if not all(math.isfinite(value) for value in (total_time, dt)):
            raise ValueError("Reachability inputs must be finite")
        if total_time < 0.0:
            raise ValueError("total_time must be non-negative")
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        current_state = state
        elapsed_time = 0.0

        while elapsed_time < total_time:
            step_dt = min(dt, total_time - elapsed_time)
            current_state = KinematicPropagator.step(current_state, dt=step_dt)
            elapsed_time += step_dt

            if current_state.mass <= PerformanceEnvelope.OEW:
                return ReachabilityEnvelope._propagate_glide(
                    current_state, total_time - elapsed_time, dt
                )

        return current_state

    @staticmethod
    def _propagate_glide(
        state: AircraftState, remaining_time: float, dt: float
    ) -> AircraftState:
        current_state = state
        elapsed_time = 0.0

        while elapsed_time < remaining_time and current_state.altitude > 0.0:
            step_dt = min(dt, remaining_time - elapsed_time)
            current_state = KinematicPropagator.step(
                current_state,
                dt=step_dt,
                climb_rate=ReachabilityEnvelope.GLIDE_DESCENT_RATE,
            )
            elapsed_time += step_dt

        return current_state
