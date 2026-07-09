"""Tests for deterministic trajectory assembly and consistency checks."""

import math

import pytest

from mh370_inverse_inference.aircraft.state import AircraftState
from mh370_inverse_inference.trajectory.consistency import (
    TrajectoryLimits,
    TrajectoryPoint,
    evaluate_trajectory,
)


def _state(
    *,
    latitude: float,
    longitude: float,
    altitude: float = 10_000.0,
    speed_tas: float = 240.0,
    heading: float = 0.0,
    mass: float = 200_000.0,
) -> AircraftState:
    return AircraftState(
        timestamp_utc="2014-03-08T18:22:00Z",
        latitude_deg=math.degrees(latitude),
        longitude_deg=math.degrees(longitude),
        altitude_m=altitude,
        true_airspeed_mps=speed_tas,
        heading_deg=math.degrees(heading),
        mass_kg=mass,
        model_version="L1.1-test",
    )


def _limits(*, require_admissibility: bool = False) -> TrajectoryLimits:
    return TrajectoryLimits(
        max_ground_speed_mps=300.0,
        max_abs_climb_rate_mps=20.0,
        max_abs_turn_rate_rad_s=0.02,
        max_mass_increase_kg=0.0,
        require_candidate_admissibility=require_admissibility,
    )


def test_consistent_two_point_trajectory_passes() -> None:
    evaluation = evaluate_trajectory(
        (
            TrajectoryPoint(
                timestamp_s=0.0,
                state=_state(latitude=0.0, longitude=0.0, mass=200_000.0),
            ),
            TrajectoryPoint(
                timestamp_s=600.0,
                state=_state(
                    latitude=math.radians(1.0),
                    longitude=0.0,
                    altitude=10_600.0,
                    heading=0.01,
                    mass=199_000.0,
                ),
            ),
        ),
        _limits(),
    )

    assert evaluation.consistent
    assert len(evaluation.segments) == 1
    segment = evaluation.segments[0]
    assert segment.speed_ok
    assert segment.climb_ok
    assert segment.turn_ok
    assert segment.mass_ok


def test_non_increasing_timestamps_fail_closed() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        evaluate_trajectory(
            (
                TrajectoryPoint(
                    timestamp_s=10.0,
                    state=_state(latitude=0.0, longitude=0.0),
                ),
                TrajectoryPoint(
                    timestamp_s=10.0,
                    state=_state(latitude=0.0, longitude=0.0),
                ),
            ),
            _limits(),
        )


def test_excessive_implied_ground_speed_is_rejected() -> None:
    evaluation = evaluate_trajectory(
        (
            TrajectoryPoint(
                timestamp_s=0.0,
                state=_state(latitude=0.0, longitude=0.0),
            ),
            TrajectoryPoint(
                timestamp_s=60.0,
                state=_state(latitude=math.radians(10.0), longitude=0.0),
            ),
        ),
        _limits(),
    )

    assert not evaluation.consistent
    assert not evaluation.segments[0].speed_ok


def test_mass_increase_is_rejected() -> None:
    evaluation = evaluate_trajectory(
        (
            TrajectoryPoint(
                timestamp_s=0.0,
                state=_state(latitude=0.0, longitude=0.0, mass=200_000.0),
            ),
            TrajectoryPoint(
                timestamp_s=600.0,
                state=_state(latitude=0.0, longitude=0.0, mass=200_001.0),
            ),
        ),
        _limits(),
    )

    assert not evaluation.consistent
    assert not evaluation.segments[0].mass_ok


def test_heading_wrap_uses_shortest_turn() -> None:
    evaluation = evaluate_trajectory(
        (
            TrajectoryPoint(
                timestamp_s=0.0,
                state=_state(
                    latitude=0.0,
                    longitude=0.0,
                    heading=math.radians(359.0),
                ),
            ),
            TrajectoryPoint(
                timestamp_s=10.0,
                state=_state(
                    latitude=0.0,
                    longitude=0.0,
                    heading=math.radians(1.0),
                ),
            ),
        ),
        _limits(),
    )

    assert evaluation.segments[0].turn_ok
    assert evaluation.segments[0].metrics.turn_rate_rad_s == pytest.approx(
        math.radians(2.0) / 10.0
    )


def test_required_endpoint_admissibility_is_enforced() -> None:
    evaluation = evaluate_trajectory(
        (
            TrajectoryPoint(
                timestamp_s=0.0,
                state=_state(latitude=0.0, longitude=0.0),
                candidate_admissible=True,
            ),
            TrajectoryPoint(
                timestamp_s=600.0,
                state=_state(latitude=0.0, longitude=0.0),
                candidate_admissible=False,
            ),
        ),
        _limits(require_admissibility=True),
    )

    assert not evaluation.consistent
    assert evaluation.segments[0].endpoints_admissible is False


def test_trajectory_requires_two_points() -> None:
    with pytest.raises(ValueError, match="at least two"):
        evaluate_trajectory(
            (
                TrajectoryPoint(
                    timestamp_s=0.0,
                    state=_state(latitude=0.0, longitude=0.0),
                ),
            ),
            _limits(),
        )
