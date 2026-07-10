"""Regression tests for frozen L1.2 fixed-step dynamics fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest

from mh370_inverse_inference.aircraft.dynamics import (
    DynamicsControlInput,
    DynamicsRequest,
)
from mh370_inverse_inference.aircraft.propagator import propagate
from mh370_inverse_inference.aircraft.state import AircraftState

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dynamics"
ABS_TOL = 1e-12
REL_TOL = 1e-12


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        loaded = json.load(source)
    assert isinstance(loaded, dict)
    return loaded


def build_request(payload: dict[str, Any]) -> DynamicsRequest:
    state_payload = payload["initial_state"]
    control_payload = payload["control_input"]
    assert isinstance(state_payload, dict)
    assert isinstance(control_payload, dict)
    return DynamicsRequest(
        initial_state=AircraftState(**state_payload),
        control_input=DynamicsControlInput(**control_payload),
        dt_seconds=float(payload["dt_seconds"]),
        model_version=str(payload["model_version"]),
    )


@pytest.mark.parametrize("case_name", ["straight_level_001", "climb_001", "turn_001"])
def test_fixed_step_fixture(case_name: str) -> None:
    request_payload = load_json(FIXTURE_DIR / f"{case_name}.input.json")
    expected_payload = load_json(FIXTURE_DIR / f"{case_name}.expected.json")
    expected_state = expected_payload["next_state"]
    assert isinstance(expected_state, dict)

    result = propagate(build_request(request_payload))
    actual_state = result.next_state.to_payload()

    for key in (
        "altitude_m",
        "heading_deg",
        "latitude_deg",
        "longitude_deg",
        "mass_kg",
        "true_airspeed_mps",
    ):
        assert actual_state[key] == pytest.approx(
            expected_state[key],
            abs=ABS_TOL,
            rel=REL_TOL,
        )

    for key in ("model_version", "timestamp_utc"):
        assert actual_state[key] == expected_state[key]

    assert len(result.input_hash) == 64
    assert len(result.output_hash) == 64
    assert len(result.op_signature_hash) == 64
