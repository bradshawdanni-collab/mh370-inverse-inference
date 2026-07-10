"""Tests for deterministic L1.3 control bounds."""

import math

import pytest

from mh370_inverse_inference.aircraft.envelope import ControlBounds


def test_control_grid_order_is_stable() -> None:
    bounds = ControlBounds(
        min_climb_rate_mps=-1.0,
        max_climb_rate_mps=1.0,
        min_turn_rate_degps=-0.5,
        max_turn_rate_degps=0.5,
        min_true_airspeed_mps=200.0,
        max_true_airspeed_mps=220.0,
        control_step_count=2,
    )

    first = bounds.controls()
    second = bounds.controls()

    assert first == second
    assert len(first) == 8
    assert first[0].to_payload() == {
        "climb_rate_mps": -1.0,
        "target_true_airspeed_mps": 200.0,
        "turn_rate_degps": -0.5,
    }
    assert first[-1].to_payload() == {
        "climb_rate_mps": 1.0,
        "target_true_airspeed_mps": 220.0,
        "turn_rate_degps": 0.5,
    }


def test_invalid_control_bounds_fail_closed() -> None:
    with pytest.raises(ValueError, match="lower bound"):
        ControlBounds(
            min_climb_rate_mps=1.0,
            max_climb_rate_mps=-1.0,
            min_turn_rate_degps=0.0,
            max_turn_rate_degps=0.0,
            min_true_airspeed_mps=200.0,
            max_true_airspeed_mps=200.0,
            control_step_count=1,
        )


def test_non_finite_control_bound_fails_closed() -> None:
    with pytest.raises(ValueError, match="finite"):
        ControlBounds(
            min_climb_rate_mps=math.nan,
            max_climb_rate_mps=1.0,
            min_turn_rate_degps=0.0,
            max_turn_rate_degps=0.0,
            min_true_airspeed_mps=200.0,
            max_true_airspeed_mps=200.0,
            control_step_count=1,
        )
