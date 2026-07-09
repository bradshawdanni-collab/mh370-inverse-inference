"""Conversion of external radar records into L1 aircraft states."""

import json
import math
from typing import Any

from mh370_inverse_inference.aircraft.state import AircraftState


class AircraftStateFactory:
    """Create validated aircraft states from external records."""

    @staticmethod
    def from_radar_json(json_str: str) -> AircraftState:
        """Transform a radar JSON record from degrees/feet/knots into SI units."""
        raw: Any = json.loads(json_str)
        if not isinstance(raw, dict):
            raise ValueError("Radar JSON must contain an object")

        try:
            coordinates = raw["coordinates"]
            if not isinstance(coordinates, dict):
                raise TypeError
            latitude_deg = float(coordinates["latitude_deg"])
            longitude_deg = float(coordinates["longitude_deg"])
            altitude_ft = float(raw["altitude_ft"])
            ground_speed_knots = float(raw["ground_speed_knots"])
            true_heading_deg = float(raw["true_heading_deg"])
            mass_kg = float(raw["estimated_aircraft_mass_kg"])
            timestamp_utc = str(raw.get("timestamp_utc", "1970-01-01T00:00:00Z"))
            model_version = str(raw.get("model_version", "L1.1-radar-factory"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Radar JSON lacks required numeric fields") from exc

        if not -90.0 <= latitude_deg <= 90.0:
            raise ValueError("Radar latitude must be between -90 and 90 degrees")
        if not all(
            math.isfinite(value)
            for value in (
                latitude_deg,
                longitude_deg,
                altitude_ft,
                ground_speed_knots,
                true_heading_deg,
                mass_kg,
            )
        ):
            raise ValueError("Radar values must be finite")

        return AircraftState(
            timestamp_utc=timestamp_utc,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            altitude_m=altitude_ft * 0.3048,
            true_airspeed_mps=ground_speed_knots * 0.514444,
            heading_deg=true_heading_deg,
            mass_kg=mass_kg,
            model_version=model_version,
        )
