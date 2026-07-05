"""Tests for the L8.4 explicit-PRNG stochastic diffusion primitive."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from mh370_inverse_inference.drift.diffusion import compute_stochastic_perturbation


def test_zero_diffusion_returns_zero_without_advancing_prng() -> None:
    prng = np.random.default_rng(seed=42)
    state_before = deepcopy(prng.bit_generator.state)

    result = compute_stochastic_perturbation(
        lat=-30.0,
        k_diffusion=0.0,
        dt=3600.0,
        prng=prng,
    )

    assert result.delta_lat == 0.0
    assert result.delta_lon == 0.0
    assert result.dx_meters == 0.0
    assert result.dy_meters == 0.0
    assert prng.bit_generator.state == state_before


def test_zero_duration_returns_zero_without_advancing_prng() -> None:
    prng = np.random.default_rng(seed=42)
    state_before = deepcopy(prng.bit_generator.state)

    result = compute_stochastic_perturbation(
        lat=-30.0,
        k_diffusion=10.0,
        dt=0.0,
        prng=prng,
    )

    assert result.delta_lat == 0.0
    assert result.delta_lon == 0.0
    assert prng.bit_generator.state == state_before


def test_identical_seeds_produce_identical_perturbations() -> None:
    first = compute_stochastic_perturbation(
        lat=-35.0,
        k_diffusion=10.0,
        dt=3600.0,
        prng=np.random.default_rng(seed=1001),
    )
    second = compute_stochastic_perturbation(
        lat=-35.0,
        k_diffusion=10.0,
        dt=3600.0,
        prng=np.random.default_rng(seed=1001),
    )

    assert first == second


def test_reused_prng_advances_between_nonzero_calls() -> None:
    prng = np.random.default_rng(seed=42)
    parameters = {
        "lat": -35.0,
        "k_diffusion": 10.0,
        "dt": 3600.0,
    }

    first = compute_stochastic_perturbation(**parameters, prng=prng)
    second = compute_stochastic_perturbation(**parameters, prng=prng)

    assert first != second


def test_sampled_displacements_match_injected_generator_sequence() -> None:
    seed = 77
    k_diffusion = 12.5
    dt = 1800.0
    expected_prng = np.random.default_rng(seed=seed)
    sigma = np.sqrt(2.0 * k_diffusion * dt)
    expected_dx = float(expected_prng.normal(loc=0.0, scale=sigma))
    expected_dy = float(expected_prng.normal(loc=0.0, scale=sigma))

    result = compute_stochastic_perturbation(
        lat=0.0,
        k_diffusion=k_diffusion,
        dt=dt,
        prng=np.random.default_rng(seed=seed),
    )

    assert result.dx_meters == expected_dx
    assert result.dy_meters == expected_dy


def test_result_is_immutable() -> None:
    result = compute_stochastic_perturbation(
        lat=0.0,
        k_diffusion=1.0,
        dt=1.0,
        prng=np.random.default_rng(seed=1),
    )

    with pytest.raises(FrozenInstanceError):
        result.delta_lat = 0.0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"lat": float("nan")}, "finite"),
        ({"lat": 91.0}, "latitude"),
        ({"k_diffusion": -1.0}, "non-negative"),
        ({"dt": -1.0}, "dt"),
        ({"lat": 90.0}, "poles"),
    ],
)
def test_invalid_inputs_fail_closed(overrides: dict[str, float], message: str) -> None:
    arguments = {
        "lat": 0.0,
        "k_diffusion": 10.0,
        "dt": 3600.0,
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        compute_stochastic_perturbation(
            **arguments,
            prng=np.random.default_rng(seed=42),
        )
