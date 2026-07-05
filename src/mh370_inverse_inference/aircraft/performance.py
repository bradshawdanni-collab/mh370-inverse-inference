"""Simplified B777-200ER performance constraints for L1 reachability."""

import math


class PerformanceEnvelope:
    """Aerodynamic, altitude, mass, and fuel-flow bounds."""

    MAX_ALTITUDE = 13_106.4
    MIN_ALTITUDE = 0.0
    OEW = 134_800.0
    MTOW = 297_550.0
    SEA_LEVEL_SPEED_OF_SOUND = 340.294

    @staticmethod
    def get_speed_limits(altitude: float) -> tuple[float, float]:
        """Return simplified minimum and maximum TAS limits in metres/second."""
        if not math.isfinite(altitude):
            raise ValueError("Altitude must be finite")
        if altitude < 0.0:
            raise ValueError("Altitude must be non-negative")

        if altitude < 11_000.0:
            temperature = 288.15 - 0.0065 * altitude
        else:
            temperature = 216.65

        speed_of_sound = PerformanceEnvelope.SEA_LEVEL_SPEED_OF_SOUND * (
            temperature / 288.15
        ) ** 0.5
        return 0.40 * speed_of_sound, 0.89 * speed_of_sound

    @classmethod
    def validate_state(cls, altitude: float, speed_tas: float, mass: float) -> bool:
        """Return whether a candidate state lies within the L1 envelope."""
        if not all(math.isfinite(value) for value in (altitude, speed_tas, mass)):
            return False
        if not (cls.MIN_ALTITUDE <= altitude <= cls.MAX_ALTITUDE):
            return False
        if not (cls.OEW <= mass <= cls.MTOW):
            return False
        min_speed, max_speed = cls.get_speed_limits(altitude)
        return min_speed <= speed_tas <= max_speed

    @classmethod
    def calculate_fuel_flow(
        cls, altitude: float, speed_tas: float, mass: float
    ) -> float:
        """Return a deterministic coarse fuel-flow estimate in kilograms/second."""
        if not all(math.isfinite(value) for value in (altitude, speed_tas, mass)):
            raise ValueError("Fuel-flow inputs must be finite")
        if altitude < 0.0 or speed_tas < 0.0 or mass <= 0.0:
            raise ValueError("Fuel-flow inputs are outside physical bounds")
        if mass <= cls.OEW:
            return 0.0

        base_rate = 1.95
        mass_factor = mass / cls.MTOW
        altitude_factor = (
            1.0 + max(0.0, (10_000.0 - altitude) / 10_000.0) * 0.5
        )
        return base_rate * mass_factor * altitude_factor
