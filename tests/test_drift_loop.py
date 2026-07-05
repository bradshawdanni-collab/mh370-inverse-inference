"""Tests for the L8.3 deterministic trajectory integration loop."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.drift.loop import integrate_trajectory
from mh370_inverse_inference.drift.step import compute_deterministic_step


def test_asymmetric_sequences_fail_before_integration() -> None:
    with pytest.raises(ValueError, match="dimension mismatch"):
        integrate_trajectory(
            init_lat=-35.0,
            init_lon=90.0,
            time_steps=[1800.0, 1800.0],
            current_vectors=[{"u": 0.1, "v": -0.1}],
            wind_vectors=[{"u": 2.0, "v": 1.0}, {"u": 1.5, "v": 0.5}],
            windage=0.01,
        )


def test_trajectory_matches_sequential_step_chain() -> None:
    first = compute_deterministic_step(
        lat=0.0,
        lon=80.0,
        u_current=0.0,
        v_current=1.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=0.0,
        dt=3600.0,
    )
    second = compute_deterministic_step(
        lat=first["lat"],
        lon=first["lon"],
        u_current=1.0,
        v_current=0.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=0.0,
        dt=3600.0,
    )

    result = integrate_trajectory(
        init_lat=0.0,
        init_lon=80.0,
        time_steps=[3600.0, 3600.0],
        current_vectors=[{"u": 0.0, "v": 1.0}, {"u": 1.0, "v": 0.0}],
        wind_vectors=[{"u": 0.0, "v": 0.0}, {"u": 0.0, "v": 0.0}],
        windage=0.0,
    )

    assert result.termination_reason == "completed"
    assert result.total_elapsed_time == 7200.0
    assert len(result.trajectory_history) == 3
    assert result.trajectory_history[1].lat == first["lat"]
    assert result.trajectory_history[1].lon == first["lon"]
    assert result.final_lat == second["lat"]
    assert result.final_lon == second["lon"]


def test_max_duration_stops_before_overrunning_step() -> None:
    result = integrate_trajectory(
        init_lat=-30.0,
        init_lon=90.0,
        time_steps=[3600.0, 3600.0, 3600.0],
        current_vectors=[{"u": 0.5, "v": 0.5}] * 3,
        wind_vectors=[{"u": 0.0, "v": 0.0}] * 3,
        windage=0.0,
        max_duration=5400.0,
    )

    assert result.termination_reason == "max_duration_breach"
    assert result.total_elapsed_time == 3600.0
    assert len(result.trajectory_history) == 2


def test_spatial_boundary_records_breach_step_then_stops() -> None:
    result = integrate_trajectory(
        init_lat=0.0,
        init_lon=90.0,
        time_steps=[3600.0, 3600.0],
        current_vectors=[{"u": 0.0, "v": 10.0}, {"u": 0.0, "v": 10.0}],
        wind_vectors=[{"u": 0.0, "v": 0.0}, {"u": 0.0, "v": 0.0}],
        windage=0.0,
        bounding_box={"lat": [-1.0, 0.1], "lon": [-180.0, 180.0]},
    )

    assert result.termination_reason == "spatial_boundary_breach"
    assert result.total_elapsed_time == 3600.0
    assert len(result.trajectory_history) == 2
    assert result.final_lat > 0.1


def test_identical_inputs_are_repeatable_and_remain_unmodified() -> None:
    time_steps = [1200.0, 1800.0]
    current_vectors = [{"u": 0.2, "v": -0.1}, {"u": 0.1, "v": 0.3}]
    wind_vectors = [{"u": 3.0, "v": 1.0}, {"u": 2.0, "v": -1.0}]
    original = deepcopy((time_steps, current_vectors, wind_vectors))

    first = integrate_trajectory(
        init_lat=-35.0,
        init_lon=95.0,
        time_steps=time_steps,
        current_vectors=current_vectors,
        wind_vectors=wind_vectors,
        windage=0.02,
    )
    second = integrate_trajectory(
        init_lat=-35.0,
        init_lon=95.0,
        time_steps=time_steps,
        current_vectors=current_vectors,
        wind_vectors=wind_vectors,
        windage=0.02,
    )

    assert first == second
    assert (time_steps, current_vectors, wind_vectors) == original
    with pytest.raises(FrozenInstanceError):
        first.trajectory_history[0].lat = 0.0


def test_invalid_bounds_and_missing_components_fail_closed() -> None:
    with pytest.raises(ValueError, match="latitude bounds"):
        integrate_trajectory(
            init_lat=0.0,
            init_lon=0.0,
            time_steps=[],
            current_vectors=[],
            wind_vectors=[],
            windage=0.0,
            bounding_box={"lat": [10.0, -10.0]},
        )

    with pytest.raises(ValueError, match="missing component"):
        integrate_trajectory(
            init_lat=0.0,
            init_lon=0.0,
            time_steps=[1.0],
            current_vectors=[{"u": 1.0}],
            wind_vectors=[{"u": 0.0, "v": 0.0}],
            windage=0.0,
        )
