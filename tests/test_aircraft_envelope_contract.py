"""Tests for the bounded L1.2 aircraft operating-envelope contract."""

from dataclasses import FrozenInstanceError, replace

import pytest

from mh370_inverse_inference.aircraft.envelope_contract import (
    AIRCRAFT_ENVELOPE_CONTRACT_VERSION,
    AircraftOperatingEnvelope,
)
from mh370_inverse_inference.provenance import ArtifactAdmissionState


def _envelope() -> AircraftOperatingEnvelope:
    return AircraftOperatingEnvelope(
        minimum_speed_mps=100.0,
        maximum_speed_mps=300.0,
        minimum_altitude_m=0.0,
        maximum_altitude_m=13_000.0,
        maximum_climb_rate_mps=20.0,
        maximum_descent_rate_mps=25.0,
        maximum_turn_rate_deg_s=3.0,
        source_id="aircraft-envelope-source",
        source_version="v1",
        model_version="b777-200er-envelope-v1",
        admission_state=ArtifactAdmissionState.PROPOSED,
    )


def test_envelope_is_immutable_and_deterministic() -> None:
    envelope = _envelope()
    assert envelope.contract_version == AIRCRAFT_ENVELOPE_CONTRACT_VERSION
    assert envelope.to_payload() == _envelope().to_payload()
    with pytest.raises(FrozenInstanceError):
        envelope.maximum_speed_mps = 301.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,value",
    (
        ("minimum_speed_mps", -1.0),
        ("maximum_speed_mps", float("nan")),
        ("minimum_altitude_m", float("inf")),
        ("maximum_altitude_m", float("-inf")),
        ("maximum_climb_rate_mps", -1.0),
        ("maximum_descent_rate_mps", -1.0),
        ("maximum_turn_rate_deg_s", -1.0),
    ),
)
def test_invalid_numeric_values_fail_closed(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        replace(_envelope(), **{field: value})


def test_inverted_bounds_fail_closed() -> None:
    with pytest.raises(ValueError, match="minimum_speed"):
        replace(_envelope(), minimum_speed_mps=301.0)
    with pytest.raises(ValueError, match="minimum_altitude"):
        replace(_envelope(), minimum_altitude_m=13_001.0)


def test_identity_and_version_fields_fail_closed() -> None:
    with pytest.raises(ValueError):
        replace(_envelope(), source_id="")
    with pytest.raises(ValueError):
        replace(_envelope(), source_version="")
    with pytest.raises(ValueError):
        replace(_envelope(), model_version="")
    with pytest.raises(ValueError):
        replace(_envelope(), contract_version="wrong")


def test_only_proposed_or_admitted_states_are_allowed() -> None:
    replace(_envelope(), admission_state=ArtifactAdmissionState.PROPOSED)
    replace(_envelope(), admission_state=ArtifactAdmissionState.ADMITTED)

    for state in (
        ArtifactAdmissionState.VERIFIED,
        ArtifactAdmissionState.REJECTED,
        ArtifactAdmissionState.SUPERSEDED,
    ):
        with pytest.raises(ValueError, match="PROPOSED or ADMITTED"):
            replace(_envelope(), admission_state=state)


def test_payload_contains_only_governed_limits_and_identity() -> None:
    payload = _envelope().to_payload()
    assert payload["admission_state"] == "PROPOSED"
    assert "fuel" not in payload
    assert "mass" not in payload
    assert "reachable" not in payload
    assert "trajectory" not in payload
