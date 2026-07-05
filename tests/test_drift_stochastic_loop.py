"""Tests for the L8.5 stochastic trajectory bridge."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from mh370_inverse_inference.drift.stochastic_loop import (
    integrate_stochastic_trajectory,
)


@pytest.fixture
def base_params() -> dict[str, Any]:
    """Return structurally symmetric forcing sequences for bridge tests."""
    return {
        "init_lat": -30.0,
        "init_lon": 95.0,
        "time_steps": [3600.0, 3600.0, 3600.0],
        "current_vectors": [{"u": 0.5, "v": 0.0}] * 3,
        "wind_vectors": [{"u": 0.0, "v": 0.0}] * 3,
        "windage": 0.0,
    }


def test_asymmetric_sequences_fail_before_integration(
    base_params: dict[str, Any],
) -> None:
    parameters = deepcopy(base_params)
    parameters["diffusion_coefficients"] = [10.0, 10.0]

    with pytest.raises(ValueError, match="dimension mismatch"):
        integrate_stochastic_trajectory(
            **parameters,
            prng=np.random.default_rng(seed=42),
        )


def test_identical_seeds_replay_exact_trajectory(
    base_params: dict[str, Any],
) -> None:
    parameters = deepcopy(base_params)
    parameters["diffusion_coefficients"] = [10.0, 15.0, 20.0]

    first = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=999),
    )
    second = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=999),
    )

    assert first == second


def test_different_seeds_diverge_for_nonzero_diffusion(
    base_params: dict[str, Any],
) -> None:
    parameters = deepcopy(base_params)
    parameters["diffusion_coefficients"] = [10.0, 10.0, 10.0]

    first = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=100),
    )
    second = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=101),
    )

    assert first.final_lat != second.final_lat
    assert first.final_lon != second.final_lon


def test_zero_diffusion_preserves_prng_tape_alignment(
    base_params: dict[str, Any],
) -> None:
    with_zero = deepcopy(base_params)
    with_zero["diffusion_coefficients"] = [10.0, 0.0, 10.0]
    history_with_zero = integrate_stochastic_trajectory(
        **with_zero,
        prng=np.random.default_rng(seed=42),
    ).trajectory_history

    active_only = deepcopy(base_params)
    active_only["time_steps"] = [3600.0, 3600.0]
    active_only["current_vectors"] = [{"u": 0.5, "v": 0.0}] * 2
    active_only["wind_vectors"] = [{"u": 0.0, "v": 0.0}] * 2
    active_only["diffusion_coefficients"] = [10.0, 10.0]
    history_active_only = integrate_stochastic_trajectory(
        **active_only,
        prng=np.random.default_rng(seed=42),
    ).trajectory_history

    assert (
        history_with_zero[3].dx_stochastic_meters
        == history_active_only[2].dx_stochastic_meters
    )
    assert (
        history_with_zero[3].dy_stochastic_meters
        == history_active_only[2].dy_stochastic_meters
    )


def test_zero_diffusion_matches_deterministic_seed_independently(
    base_params: dict[str, Any],
) -> None:
    parameters = deepcopy(base_params)
    parameters["diffusion_coefficients"] = [0.0, 0.0, 0.0]

    first = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=1),
    )
    second = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=999),
    )

    assert first == second


def test_duration_and_boundary_stops_are_deterministic(
    base_params: dict[str, Any],
) -> None:
    duration_params = deepcopy(base_params)
    duration_params["diffusion_coefficients"] = [0.0, 0.0, 0.0]
    duration_result = integrate_stochastic_trajectory(
        **duration_params,
        prng=np.random.default_rng(seed=42),
        max_duration=5400.0,
    )

    assert duration_result.termination_reason == "max_duration_breach"
    assert duration_result.total_elapsed_time == 3600.0
    assert len(duration_result.trajectory_history) == 2

    boundary_params = deepcopy(base_params)
    boundary_params["current_vectors"] = [{"u": 0.0, "v": 10.0}] * 3
    boundary_params["diffusion_coefficients"] = [0.0, 0.0, 0.0]
    boundary_result = integrate_stochastic_trajectory(
        **boundary_params,
        prng=np.random.default_rng(seed=42),
        bounding_box={"lat": [-31.0, -29.9], "lon": [-180.0, 180.0]},
    )

    assert boundary_result.termination_reason == "spatial_boundary_breach"
    assert len(boundary_result.trajectory_history) == 2


def test_result_and_history_points_are_immutable(
    base_params: dict[str, Any],
) -> None:
    parameters = deepcopy(base_params)
    parameters["diffusion_coefficients"] = [1.0, 1.0, 1.0]
    result = integrate_stochastic_trajectory(
        **parameters,
        prng=np.random.default_rng(seed=7),
    )

    assert isinstance(result.trajectory_history, tuple)
    with pytest.raises(FrozenInstanceError):
        result.trajectory_history[0].lat = 0.0
