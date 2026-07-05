"""Tests for radar-record conversion into AircraftState."""

import math

import pytest

from mh370_inverse_inference.aircraft.factory import AircraftStateFactory


def test_radar_factory_conversion() -> None:
    sample_json = """
    {
      "timestamp_utc": "2014-03-08T18:22:12Z",
      "coordinates": {"latitude_deg": 0.0, "longitude_deg": 180.0},
      "altitude_ft": 32808.39895,
      "ground_speed_knots": 194.3844,
      "true_heading_deg": 180.0,
      "estimated_aircraft_mass_kg": 200000.0
    }
    """

    state = AircraftStateFactory.from_radar_json(sample_json)

    assert state.latitude == 0.0
    assert math.isclose(abs(state.longitude), math.pi)
    assert math.isclose(state.altitude, 10_000.0, abs_tol=1e-2)
    assert math.isclose(state.speed_tas, 100.0, abs_tol=1e-2)
    assert math.isclose(state.heading, math.pi)
    assert state.mass == 200_000.0


def test_radar_factory_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="required numeric fields"):
        AircraftStateFactory.from_radar_json('{"coordinates": {}}')
