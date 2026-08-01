"""Immutable aircraft state records for L1 dynamics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def _validate_timestamp(value: str) -> None:
    if not value.endswith("Z"):
        raise ValueError("timestamp_utc must end with Z")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must be UTC")


def _finite(value: float, name: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved):
        raise ValueError(f"{name} must be finite")
    return resolved


@dataclass(frozen=True, slots=True)
class AircraftState:
    """Immutable canonical aircraft state value object."""

    timestamp_utc: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    true_airspeed_mps: float
    heading_deg: float
    mass_kg: float
    model_version: str

    def __post_init__(self) -> None:
        _validate_timestamp(self.timestamp_utc)
        latitude = _finite(self.latitude_deg, "latitude_deg")
        longitude = _finite(self.longitude_deg, "longitude_deg")
        altitude = _finite(self.altitude_m, "altitude_m")
        speed = _finite(self.true_airspeed_mps, "true_airspeed_mps")
        heading = _finite(self.heading_deg, "heading_deg")
        mass = _finite(self.mass_kg, "mass_kg")

        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude_deg must be between -90 and 90")
        if altitude < 0.0:
            raise ValueError("altitude_m cannot be negative")
        if speed < 0.0:
            raise ValueError("true_airspeed_mps cannot be negative")
        if mass <= 0.0:
            raise ValueError("mass_kg must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")

        object.__setattr__(self, "latitude_deg", latitude)
        object.__setattr__(self, "longitude_deg", ((longitude + 180.0) % 360.0) - 180.0)
        object.__setattr__(self, "altitude_m", altitude)
        object.__setattr__(self, "true_airspeed_mps", speed)
        object.__setattr__(self, "heading_deg", heading % 360.0)
        object.__setattr__(self, "mass_kg", mass)

    @property
    def latitude(self) -> float:
        """Latitude in radians."""
        return math.radians(self.latitude_deg)

    @property
    def longitude(self) -> float:
        """Longitude in radians."""
        return math.radians(self.longitude_deg)

    @property
    def altitude(self) -> float:
        """Altitude in metres."""
        return self.altitude_m

    @property
    def speed_tas(self) -> float:
        """True airspeed in m/s."""
        return self.true_airspeed_mps

    @property
    def heading(self) -> float:
        """Heading in radians."""
        return math.radians(self.heading_deg)

    @property
    def mass(self) -> float:
        """Mass in kg."""
        return self.mass_kg

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible state payload."""
        return {
            "altitude_m": self.altitude_m,
            "heading_deg": self.heading_deg,
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "mass_kg": self.mass_kg,
            "model_version": self.model_version,
            "timestamp_utc": self.timestamp_utc,
            "true_airspeed_mps": self.true_airspeed_mps,
        }
