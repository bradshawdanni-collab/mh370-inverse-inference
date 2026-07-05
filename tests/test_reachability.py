"""Tests for L1 fuel-constrained reachability."""

import math

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.reachability import ReachabilityEnvelope
from mh370_inverse_inference.aircraft.state import AircraftState


def test_reachability_fuel_exhaustion() -> None:
    initial_state = AircraftState(
        latitude=0.0,
        longitude=0.0,
        altitude=10_000.0,
        speed_tas=240.0,
        heading=0.0,
        mass=PerformanceEnvelope.OEW + 200.0,
    )

    final_state = ReachabilityEnvelope.compute_max_range_step(
        initial_state, total_time=3_600.0, dt=10.0
    )

    assert math.isclose(final_state.mass, PerformanceEnvelope.OEW)
    assert final_state.altitude == 0.0
    assert final_state.latitude > initial_state.latitude
