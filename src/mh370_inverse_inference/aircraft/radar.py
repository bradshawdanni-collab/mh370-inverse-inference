"""Deterministic radar-track input schema for Issue #83."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mh370_inverse_inference.provenance import (
    ArtifactAdmissionState,
    ProvenanceRegistrySnapshot,
    lookup_record,
)

RADAR_INPUT_CONTRACT_VERSION = "RADAR-INPUT-1"


@dataclass(frozen=True, slots=True)
class RadarUncertainty:
    """Explicit uncertainty bounds for one radar observation."""

    position_m: float
    speed_mps: float
    heading_deg: float

    def __post_init__(self) -> None:
        for name, value in (
            ("position_m", self.position_m),
            ("speed_mps", self.speed_mps),
            ("heading_deg", self.heading_deg),
        ):
            if type(value) not in (int, float):
                raise TypeError(f"{name} must be numeric")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

    def to_payload(self) -> dict[str, float]:
        return {
            "heading_deg": float(self.heading_deg),
            "position_m": float(self.position_m),
            "speed_mps": float(self.speed_mps),
        }


@dataclass(frozen=True, slots=True)
class RadarTrackPoint:
    """One validated, provenance-bound radar observation."""

    timestamp_utc: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    groundspeed_mps: float
    heading_deg: float
    source_id: str
    source_version: str
    uncertainty: RadarUncertainty
    contract_version: str = RADAR_INPUT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _validate_timestamp(self.timestamp_utc)
        _validate_range("latitude_deg", self.latitude_deg, -90.0, 90.0)
        _validate_range("longitude_deg", self.longitude_deg, -180.0, 180.0)
        if type(self.altitude_m) not in (int, float):
            raise TypeError("altitude_m must be numeric")
        if type(self.groundspeed_mps) not in (int, float):
            raise TypeError("groundspeed_mps must be numeric")
        if self.groundspeed_mps < 0:
            raise ValueError("groundspeed_mps must be non-negative")
        _validate_range(
            "heading_deg",
            self.heading_deg,
            0.0,
            360.0,
            upper_open=True,
        )
        if not self.source_id.strip():
            raise ValueError("source_id cannot be blank")
        if not self.source_version.strip():
            raise ValueError("source_version cannot be blank")
        if type(self.uncertainty) is not RadarUncertainty:
            raise TypeError("uncertainty must be RadarUncertainty")
        if self.contract_version != RADAR_INPUT_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {RADAR_INPUT_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
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
            "uncertainty": self.uncertainty.to_payload(),
        }


def validate_radar_source(
    point: RadarTrackPoint,
    registry_snapshot: ProvenanceRegistrySnapshot,
) -> None:
    """Fail closed unless source_id/version resolves to a governed record."""
    record = lookup_record(registry_snapshot, point.source_id, point.source_version)
    if record is None:
        raise ValueError("radar source is not present in the provenance registry")
    if record.admission_state not in (
        ArtifactAdmissionState.PROPOSED,
        ArtifactAdmissionState.ADMITTED,
    ):
        raise ValueError("radar source must be PROPOSED or ADMITTED")


def _validate_timestamp(value: str) -> None:
    if type(value) is not str:
        raise TypeError("timestamp_utc must be a string")
    if not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("timestamp_utc must be valid ISO 8601 UTC") from exc
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")


def _validate_range(
    name: str,
    value: float,
    lower: float,
    upper: float,
    *,
    upper_open: bool = False,
) -> None:
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be numeric")
    valid = lower <= value < upper if upper_open else lower <= value <= upper
    if not valid:
        comparator = f"[{lower}, {upper})" if upper_open else f"[{lower}, {upper}]"
        raise ValueError(f"{name} must be within {comparator}")
