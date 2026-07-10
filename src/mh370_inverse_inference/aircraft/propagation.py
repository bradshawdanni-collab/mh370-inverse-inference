"""Great-circle aircraft state propagation for L1."""

import math
from datetime import datetime, timedelta

from mh370_inverse_inference.aircraft.performance import PerformanceEnvelope
from mh370_inverse_inference.aircraft.state import AircraftState


class KinematicPropagator:
    """Forward-integrate an aircraft state with a spherical-Earth model."""

    EARTH_RADIUS = 6_371_000.0

    @classmethod
    def step(
        cls,
        state: AircraftState,
        dt: float,
        climb_rate: float = 0.0,
        turn_rate: float = 0.0,
    ) -> AircraftState:
        """Advance one deterministic integration step."""
        if not all(math.isfinite(value) for value in (dt, climb_rate, turn_rate)):
            raise ValueError("Propagation inputs must be finite")
        if dt <= 0.0:
            raise ValueError("dt must be positive")

        fuel_flow = PerformanceEnvelope.calculate_fuel_flow(
            state.altitude, state.speed_tas, state.mass
        )
        new_mass = max(PerformanceEnvelope.OEW, state.mass - fuel_flow * dt)
        new_altitude = max(
            0.0,
            min(
                PerformanceEnvelope.MAX_ALTITUDE,
                state.altitude + climb_rate * dt,
            ),
        )
        new_heading = (state.heading + turn_rate * dt) % (2 * math.pi)

        min_speed, max_speed = PerformanceEnvelope.get_speed_limits(new_altitude)
        new_speed = max(min_speed, min(max_speed, state.speed_tas))
        angular_distance = new_speed * dt / cls.EARTH_RADIUS

        latitude_2 = math.asin(
            math.sin(state.latitude) * math.cos(angular_distance)
            + math.cos(state.latitude)
            * math.sin(angular_distance)
            * math.cos(new_heading)
        )
        longitude_2 = state.longitude + math.atan2(
            math.sin(new_heading)
            * math.sin(angular_distance)
            * math.cos(state.latitude),
            math.cos(angular_distance)
            - math.sin(state.latitude) * math.sin(latitude_2),
        )
        timestamp = datetime.fromisoformat(
            state.timestamp_utc.removesuffix("Z") + "+00:00"
        ) + timedelta(seconds=dt)

        return AircraftState(
            timestamp_utc=timestamp.isoformat().replace("+00:00", "Z"),
            latitude_deg=math.degrees(latitude_2),
            longitude_deg=math.degrees(longitude_2),
            altitude_m=new_altitude,
            true_airspeed_mps=new_speed,
            heading_deg=math.degrees(new_heading),
            mass_kg=new_mass,
            model_version=state.model_version,
        )
