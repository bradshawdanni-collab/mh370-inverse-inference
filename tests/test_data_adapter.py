"""Tests for deterministic environmental grid interpolation."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from mh370_inverse_inference.data.adapter import EnvironmentalGridAdapter


@pytest.fixture
def synthetic_grid() -> EnvironmentalGridAdapter:
    times = np.array([0.0, 3600.0])
    lats = np.array([-35.0, -34.0])
    lons = np.array([90.0, 91.0])
    u_grid = np.full((2, 2, 2), 0.5)
    v_grid = np.full((2, 2, 2), -0.2)
    u_grid[1, 1, 1] = 1.5
    return EnvironmentalGridAdapter(times, lats, lons, u_grid, v_grid)


def test_center_trilinear_interpolation(
    synthetic_grid: EnvironmentalGridAdapter,
) -> None:
    sample = synthetic_grid.sample_vector(t=1800.0, lat=-34.5, lon=90.5)

    assert sample.u == pytest.approx(0.625)
    assert sample.v == pytest.approx(-0.2)


def test_exact_upper_boundary_is_supported(
    synthetic_grid: EnvironmentalGridAdapter,
) -> None:
    sample = synthetic_grid.sample_vector(t=3600.0, lat=-34.0, lon=91.0)

    assert sample.u == 1.5
    assert sample.v == -0.2


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ({"t": -1.0, "lat": -34.5, "lon": 90.5}, "temporal"),
        ({"t": 0.0, "lat": -36.0, "lon": 90.5}, "latitude"),
        ({"t": 0.0, "lat": -34.5, "lon": 92.0}, "longitude"),
        ({"t": float("nan"), "lat": -34.5, "lon": 90.5}, "finite"),
    ],
)
def test_out_of_bounds_queries_fail_closed(
    synthetic_grid: EnvironmentalGridAdapter,
    query: dict[str, float],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        synthetic_grid.sample_vector(**query)


def test_adapter_copies_source_arrays() -> None:
    times = np.array([0.0, 1.0])
    lats = np.array([0.0, 1.0])
    lons = np.array([10.0, 11.0])
    u_grid = np.ones((2, 2, 2))
    v_grid = np.zeros((2, 2, 2))
    adapter = EnvironmentalGridAdapter(times, lats, lons, u_grid, v_grid)

    u_grid[:] = 99.0
    sample = adapter.sample_vector(t=0.5, lat=0.5, lon=10.5)

    assert sample.u == 1.0


def test_sample_result_is_immutable(synthetic_grid: EnvironmentalGridAdapter) -> None:
    sample = synthetic_grid.sample_vector(t=0.0, lat=-35.0, lon=90.0)

    with pytest.raises(FrozenInstanceError):
        sample.u = 0.0


@pytest.mark.parametrize(
    ("times", "lats", "lons", "message"),
    [
        ([0.0], [-35.0, -34.0], [90.0, 91.0], "at least two"),
        ([0.0, 0.0], [-35.0, -34.0], [90.0, 91.0], "strictly increasing"),
        ([0.0, 1.0], [-34.0, -35.0], [90.0, 91.0], "strictly increasing"),
        ([0.0, 1.0], [-35.0, -34.0], [179.0, 181.0], "longitude axis"),
    ],
)
def test_invalid_axes_fail_closed(
    times: list[float],
    lats: list[float],
    lons: list[float],
    message: str,
) -> None:
    shape = (len(times), len(lats), len(lons))
    with pytest.raises(ValueError, match=message):
        EnvironmentalGridAdapter(
            times,
            lats,
            lons,
            np.zeros(shape),
            np.zeros(shape),
        )


def test_grid_shape_and_finiteness_are_validated() -> None:
    with pytest.raises(ValueError, match="shape mismatch"):
        EnvironmentalGridAdapter(
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
            np.zeros((2, 2, 1)),
            np.zeros((2, 2, 2)),
        )

    invalid = np.zeros((2, 2, 2))
    invalid[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="grid values must be finite"):
        EnvironmentalGridAdapter(
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
            invalid,
            np.zeros((2, 2, 2)),
        )
