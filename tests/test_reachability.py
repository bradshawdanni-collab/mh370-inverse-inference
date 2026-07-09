"""Tests for L1 fuel-constrained reachability."""

import math

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.reachability import ReachabilityEnvelope
from mh370_inverse_inference.aircraft.state import AircraftState


def test_reachability_fuel_exhaustion() -> None:
    initial_state = AircraftState(
        timestamp_utc="2014-03-08T18:22:00Z",
        latitude_deg=0.0,
        longitude_deg=0.0,
        altitude_m=10_000.0,
        true_airspeed_mps=240.0,
        heading_deg=0.0,
        mass_kg=PerformanceEnvelope.OEW + 200.0,
        model_version="L1.1-test",
    )

    final_state = ReachabilityEnvelope.compute_max_range_step(
        initial_state, total_time=3_600.0, dt=10.0
    )

    assert math.isclose(final_state.mass, PerformanceEnvelope.OEW)
    assert final_state.altitude == 0.0
    assert final_state.latitude > initial_state.latitude
