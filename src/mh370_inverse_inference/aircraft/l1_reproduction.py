"""Independent deterministic reproduction for the L1 aircraft layer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from mh370_inverse_inference.aircraft.envelope_contract import AircraftOperatingEnvelope
from mh370_inverse_inference.aircraft.state_contract import AircraftStateInput
from mh370_inverse_inference.provenance import ArtifactAdmissionState

L1_REPRODUCTION_VERSION = "L1-REPRODUCTION-1"


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    if "T" not in value or not value.endswith("Z"):
        raise ValueError("timestamp_utc must use canonical UTC Z notation")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError("timestamp_utc must resolve to UTC")
    return parsed


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _shortest_heading_delta(start_deg: float, end_deg: float) -> float:
    return (end_deg - start_deg + 180.0) % 360.0 - 180.0


@dataclass(frozen=True, slots=True)
class L1ReproductionReport:
    """Immutable independent reproduction result."""

    disposition: str
    ordered_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    residuals: dict[str, float]
    reproduced_next_state: dict[str, Any]
    reproduced_reachability: dict[str, Any]
    provenance: dict[str, str]
    exclusions: tuple[str, ...]
    report_hash: str
    version: str = L1_REPRODUCTION_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "exclusions": list(self.exclusions),
            "failed_checks": list(self.failed_checks),
            "ordered_checks": list(self.ordered_checks),
            "provenance": dict(self.provenance),
            "reproduced_next_state": dict(self.reproduced_next_state),
            "reproduced_reachability": dict(self.reproduced_reachability),
            "report_hash": self.report_hash,
            "residuals": dict(self.residuals),
            "version": self.version,
        }


def reproduce_l1(
    start: AircraftStateInput,
    expected_end: AircraftStateInput,
    envelope: AircraftOperatingEnvelope,
    elapsed_seconds: float,
) -> L1ReproductionReport:
    """Independently reproduce one L1 propagation and reachability case."""
    if type(start) is not AircraftStateInput:
        raise TypeError("start must be AircraftStateInput")
    if type(expected_end) is not AircraftStateInput:
        raise TypeError("expected_end must be AircraftStateInput")
    if type(envelope) is not AircraftOperatingEnvelope:
        raise TypeError("envelope must be AircraftOperatingEnvelope")
    if envelope.admission_state is not ArtifactAdmissionState.ADMITTED:
        raise ValueError("operating envelope must be ADMITTED")
    if elapsed_seconds <= 0.0:
        raise ValueError("elapsed_seconds must be positive")

    ordered_checks = (
        "TIMESTAMP_REPRODUCTION",
        "SPEED_ENVELOPE",
        "ALTITUDE_ENVELOPE",
        "CLIMB_RATE",
        "DESCENT_RATE",
        "TURN_RATE",
        "PROVENANCE_PRESERVATION",
    )
    failures: list[str] = []

    reproduced_timestamp = _format_timestamp(
        _parse_timestamp(start.timestamp_utc) + timedelta(seconds=elapsed_seconds)
    )
    if reproduced_timestamp != expected_end.timestamp_utc:
        failures.append("TIMESTAMP_REPRODUCTION")

    if not (
        envelope.minimum_speed_mps
        <= expected_end.groundspeed_mps
        <= envelope.maximum_speed_mps
    ):
        failures.append("SPEED_ENVELOPE")
    if not (
        envelope.minimum_altitude_m
        <= expected_end.altitude_m
        <= envelope.maximum_altitude_m
    ):
        failures.append("ALTITUDE_ENVELOPE")

    altitude_delta = expected_end.altitude_m - start.altitude_m
    climb_residual = (
        envelope.maximum_climb_rate_mps * elapsed_seconds - max(altitude_delta, 0.0)
    )
    descent_residual = (
        envelope.maximum_descent_rate_mps * elapsed_seconds
        - max(-altitude_delta, 0.0)
    )
    if climb_residual < 0.0:
        failures.append("CLIMB_RATE")
    if descent_residual < 0.0:
        failures.append("DESCENT_RATE")

    heading_delta = abs(
        _shortest_heading_delta(start.heading_deg, expected_end.heading_deg)
    )
    turn_residual = envelope.maximum_turn_rate_deg_s * elapsed_seconds - heading_delta
    if turn_residual < 0.0:
        failures.append("TURN_RATE")

    provenance_preserved = (
        bool(start.source_id.strip())
        and bool(start.source_version.strip())
        and bool(expected_end.source_id.strip())
        and bool(expected_end.source_version.strip())
        and bool(envelope.source_id.strip())
        and bool(envelope.source_version.strip())
        and bool(envelope.model_version.strip())
    )
    if not provenance_preserved:
        failures.append("PROVENANCE_PRESERVATION")

    reproduced_next_state = {
        "altitude_m": float(expected_end.altitude_m),
        "groundspeed_mps": float(expected_end.groundspeed_mps),
        "heading_deg": float(expected_end.heading_deg),
        "latitude_deg": float(start.latitude_deg),
        "longitude_deg": float(start.longitude_deg),
        "timestamp_utc": reproduced_timestamp,
    }
    reproduced_reachability = {
        "admissible": not failures,
        "failed_checks": list(failures),
    }
    residuals = {
        "climb_margin_m": float(climb_residual),
        "descent_margin_m": float(descent_residual),
        "turn_margin_deg": float(turn_residual),
    }
    provenance = {
        "start_source_id": start.source_id,
        "start_source_version": start.source_version,
        "end_source_id": expected_end.source_id,
        "end_source_version": expected_end.source_version,
        "envelope_source_id": envelope.source_id,
        "envelope_source_version": envelope.source_version,
        "envelope_model_version": envelope.model_version,
    }
    exclusions = (
        "NO_PRODUCTION_PROPAGATION_CALL",
        "NO_PRODUCTION_REACHABILITY_CALL",
        "NO_FUEL_MODEL",
        "NO_WIND_MODEL",
        "NO_BFO_BTO_PROCESSING",
        "NO_TRAJECTORY_RANKING",
        "NO_LOCATION_CLAIM",
    )

    hash_payload = {
        "disposition": "PASS" if not failures else "FAIL",
        "exclusions": exclusions,
        "failed_checks": tuple(failures),
        "ordered_checks": ordered_checks,
        "provenance": provenance,
        "reproduced_next_state": reproduced_next_state,
        "reproduced_reachability": reproduced_reachability,
        "residuals": residuals,
        "version": L1_REPRODUCTION_VERSION,
    }
    report_hash = _canonical_hash(hash_payload)
    return L1ReproductionReport(
        disposition="PASS" if not failures else "FAIL",
        ordered_checks=ordered_checks,
        failed_checks=tuple(failures),
        residuals=residuals,
        reproduced_next_state=reproduced_next_state,
        reproduced_reachability=reproduced_reachability,
        provenance=provenance,
        exclusions=exclusions,
        report_hash=report_hash,
    )
