"""Immutable aircraft state representation for L1 dynamics."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AircraftState:
    """Kinematic and physical state of the aircraft in SI units."""

    latitude: float
    longitude: float
    altitude: float
    speed_tas: float
    heading: float
    mass: float

    def __post_init__(self) -> None:
        values = (
            self.latitude,
            self.longitude,
            self.altitude,
            self.speed_tas,
            self.heading,
            self.mass,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Aircraft state values must be finite")
        if not (-math.pi / 2 <= self.latitude <= math.pi / 2):
            raise ValueError("Latitude must be between -pi/2 and pi/2")
        if self.altitude < 0.0:
            raise ValueError("Altitude must be non-negative")
        if self.speed_tas < 0.0:
            raise ValueError("True airspeed must be non-negative")
        if self.mass <= 0.0:
            raise ValueError("Mass must be positive")

        normalized_longitude = (self.longitude + math.pi) % (2 * math.pi) - math.pi
        normalized_heading = self.heading % (2 * math.pi)
        object.__setattr__(self, "longitude", normalized_longitude)
        object.__setattr__(self, "heading", normalized_heading)
