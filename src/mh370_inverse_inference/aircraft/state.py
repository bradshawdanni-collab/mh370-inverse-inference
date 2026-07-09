"""Immutable aircraft state records for L1 dynamics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite
from typing import Any


def _require_finite(value: float, name: str) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")


def _validate_utc_timestamp(value: str) -> None:
    if not value.endswith("Z"):
        raise ValueError("timestamp_utc must use a trailing 'Z' UTC designator")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("timestamp_utc must be a valid ISO 8601 UTC timestamp") from exc
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must be UTC")


@dataclass(frozen=True, slots=True)
class AircraftState:
    """Immutable aircraft state value object.

    This record carries identity and serialization semantics only. It does not
    perform propagation, inference, or aerodynamic validation.
    """

    timestamp_utc: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    true_airspeed_mps: float
    heading_deg: float
    mass_kg: float
    model_version: str

    def __post_init__(self) -> None:
        _validate_utc_timestamp(self.timestamp_utc)
        for name in (
            "latitude_deg",
            "longitude_deg",
            "altitude_m",
            "true_airspeed_mps",
            "heading_deg",
            "mass_kg",
        ):
            _require_finite(float(getattr(self, name)), name)

        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude_deg must be between -90 and 90")
        if not -180.0 <= self.longitude_deg <= 180.0:
            raise ValueError("longitude_deg must be between -180 and 180")
        if self.altitude_m < 0.0:
            raise ValueError("altitude_m cannot be negative")
        if self.true_airspeed_mps < 0.0:
            raise ValueError("true_airspeed_mps cannot be negative")
        if not 0.0 <= self.heading_deg < 360.0:
            raise ValueError("heading_deg must be in [0, 360)")
        if self.mass_kg <= 0.0:
            raise ValueError("mass_kg must be positive")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be blank")

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
