"""Immutable aircraft state and deterministic transition contracts for L1.1."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mh370_inverse_inference.aircraft.radar import RadarTrackPoint

AIRCRAFT_STATE_CONTRACT_VERSION = "AIRCRAFT-STATE-1"


def _parse_timestamp(value: str) -> datetime:
    if type(value) is not str:
        raise TypeError("timestamp_utc must be a string")
    if "T" not in value or not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("timestamp_utc must be valid ISO 8601 UTC") from exc
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")
    return parsed


def _finite(value: float, name: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be numeric")
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
    groundspeed_mps: float
    heading_deg: float
    source_id: str
    source_version: str
    contract_version: str = AIRCRAFT_STATE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _parse_timestamp(self.timestamp_utc)
        latitude = _finite(self.latitude_deg, "latitude_deg")
        longitude = _finite(self.longitude_deg, "longitude_deg")
        altitude = _finite(self.altitude_m, "altitude_m")
        speed = _finite(self.groundspeed_mps, "groundspeed_mps")
        heading = _finite(self.heading_deg, "heading_deg")

        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude_deg must be between -90 and 90")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude_deg must be between -180 and 180")
        if altitude < 0.0:
            raise ValueError("altitude_m cannot be negative")
        if speed < 0.0:
            raise ValueError("groundspeed_mps cannot be negative")
        if not 0.0 <= heading < 360.0:
            raise ValueError("heading_deg must be within [0, 360)")
        if not self.source_id.strip():
            raise ValueError("source_id cannot be blank")
        if not self.source_version.strip():
            raise ValueError("source_version cannot be blank")
        if self.contract_version != AIRCRAFT_STATE_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AIRCRAFT_STATE_CONTRACT_VERSION}"
            )

    @classmethod
    def from_radar_track_point(cls, point: RadarTrackPoint) -> AircraftState:
        """Initialize state by copying one governed radar point exactly."""
        if type(point) is not RadarTrackPoint:
            raise TypeError("point must be RadarTrackPoint")
        return cls(
            timestamp_utc=point.timestamp_utc,
            latitude_deg=point.latitude_deg,
            longitude_deg=point.longitude_deg,
            altitude_m=point.altitude_m,
            groundspeed_mps=point.groundspeed_mps,
            heading_deg=point.heading_deg,
            source_id=point.source_id,
            source_version=point.source_version,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible state payload."""
        return {
            "altitude_m": float(self.altitude_m),
            "contract_version": self.contract_version,
            "groundspeed_mps": float(self.groundspeed_mps),
            "heading_deg": float(self.heading_deg),
            "latitude_deg": float(self.latitude_deg),
            "longitude_deg": float(self.longitude_deg),
            "source_id": self.source_id,
            "source_version": self.source_version,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass(frozen=True, slots=True)
class AircraftStateTransition:
    """Explicit transition description without a reachability claim."""

    previous: AircraftState
    current: AircraftState
    elapsed_seconds: float
    contract_version: str = AIRCRAFT_STATE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if type(self.previous) is not AircraftState:
            raise TypeError("previous must be AircraftState")
        if type(self.current) is not AircraftState:
            raise TypeError("current must be AircraftState")
        elapsed = _finite(self.elapsed_seconds, "elapsed_seconds")
        if elapsed <= 0.0:
            raise ValueError("elapsed_seconds must be positive")
        if self.previous.contract_version != self.current.contract_version:
            raise ValueError("state contract versions must match")
        if self.contract_version != AIRCRAFT_STATE_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {AIRCRAFT_STATE_CONTRACT_VERSION}"
            )
        previous_time = _parse_timestamp(self.previous.timestamp_utc)
        current_time = _parse_timestamp(self.current.timestamp_utc)
        if current_time <= previous_time:
            raise ValueError(
                "current state timestamp must be later than previous state"
            )
        calculated = (current_time - previous_time).total_seconds()
        if elapsed != calculated:
            raise ValueError("elapsed_seconds must match the timestamp difference")

    def to_payload(self) -> dict[str, Any]:
        """Return a canonical JSON-compatible transition payload."""
        return {
            "contract_version": self.contract_version,
            "current": self.current.to_payload(),
            "elapsed_seconds": float(self.elapsed_seconds),
            "previous": self.previous.to_payload(),
        }


def aircraft_state_from_radar(point: RadarTrackPoint) -> AircraftState:
    """Compatibility wrapper for exact governed radar initialisation."""
    return AircraftState.from_radar_track_point(point)
