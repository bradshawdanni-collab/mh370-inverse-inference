"""Tests for independent deterministic L1 reproduction."""

from mh370_inverse_inference.aircraft.envelope_contract import (
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.aircraft.l1_reproduction import reproduce_l1
from mh370_inverse_inference.aircraft.state_contract import AircraftStateInput
from mh370_inverse_inference.provenance import ArtifactAdmissionState


def _state(
    *,
    timestamp_utc: str,
    altitude_m: float = 10_000.0,
    groundspeed_mps: float = 240.0,
    heading_deg: float = 270.0,
    source_id: str = "radar-source",
    source_version: str = "v1",
) -> AircraftStateInput:
    return AircraftStateInput(
        timestamp_utc=timestamp_utc,
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=altitude_m,
        groundspeed_mps=groundspeed_mps,
        heading_deg=heading_deg,
        source_id=source_id,
        source_version=source_version,
    )


def _envelope() -> AircraftOperatingEnvelope:
    return AircraftOperatingEnvelope(
        minimum_speed_mps=180.0,
        maximum_speed_mps=280.0,
        minimum_altitude_m=0.0,
        maximum_altitude_m=13_000.0,
        maximum_climb_rate_mps=10.0,
        maximum_descent_rate_mps=12.0,
        maximum_turn_rate_deg_s=3.0,
        source_id="performance-source",
        source_version="v2",
        model_version="B777-envelope-v1",
        admission_state=ArtifactAdmissionState.ADMITTED,
    )


def test_independent_reproduction_passes_representative_case() -> None:
    report = reproduce_l1(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(
            timestamp_utc="2014-03-07T18:23:00Z",
            altitude_m=10_300.0,
            groundspeed_mps=250.0,
            heading_deg=280.0,
            source_id="radar-source-2",
            source_version="v2",
        ),
        _envelope(),
        60.0,
    )

    assert report.disposition == "PASS"
    assert report.failed_checks == ()
    assert report.reproduced_reachability["admissible"] is True
    assert len(report.report_hash) == 64


def test_independent_reproduction_is_deterministic() -> None:
    start = _state(timestamp_utc="2014-03-07T18:22:00Z")
    end = _state(timestamp_utc="2014-03-07T18:23:00Z")
    first = reproduce_l1(start, end, _envelope(), 60.0)
    second = reproduce_l1(start, end, _envelope(), 60.0)

    assert first.to_payload() == second.to_payload()


def test_independent_reproduction_reports_ordered_failures() -> None:
    report = reproduce_l1(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(
            timestamp_utc="2014-03-07T18:22:10Z",
            altitude_m=10_101.0,
            groundspeed_mps=281.0,
            heading_deg=301.0,
        ),
        _envelope(),
        10.0,
    )

    assert report.disposition == "FAIL"
    assert report.failed_checks == (
        "SPEED_ENVELOPE",
        "CLIMB_RATE",
        "TURN_RATE",
    )


def test_report_records_required_exclusions() -> None:
    report = reproduce_l1(
        _state(timestamp_utc="2014-03-07T18:22:00Z"),
        _state(timestamp_utc="2014-03-07T18:23:00Z"),
        _envelope(),
        60.0,
    )

    assert "NO_PRODUCTION_PROPAGATION_CALL" in report.exclusions
    assert "NO_PRODUCTION_REACHABILITY_CALL" in report.exclusions
    assert "NO_LOCATION_CLAIM" in report.exclusions
