"""Replayable stochastic trajectory integration for ocean drift."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

import numpy as np

from mh370_inverse_inference.drift.diffusion import compute_stochastic_perturbation
from mh370_inverse_inference.drift.step import compute_deterministic_step


@dataclass(frozen=True, slots=True)
class StochasticTrajectoryPoint:
    """One immutable point in a stochastic trajectory trace."""

    step_index: int
    elapsed_time: float
    lat: float
    lon: float
    u_effective: float
    v_effective: float
    dx_stochastic_meters: float
    dy_stochastic_meters: float


@dataclass(frozen=True, slots=True)
class StochasticTrajectoryResult:
    """Immutable result of seeded stochastic trajectory integration."""

    final_lat: float
    final_lon: float
    total_elapsed_time: float
    termination_reason: str
    trajectory_history: tuple[StochasticTrajectoryPoint, ...]


def _validated_bounds(
    bounding_box: Mapping[str, Sequence[float]] | None,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    if bounding_box is None:
        return None

    lat_values = bounding_box.get("lat", (-90.0, 90.0))
    lon_values = bounding_box.get("lon", (-180.0, 180.0))
    if len(lat_values) != 2 or len(lon_values) != 2:
        raise ValueError("bounding-box latitude and longitude ranges need two values")

    lat_bounds = (float(lat_values[0]), float(lat_values[1]))
    lon_bounds = (float(lon_values[0]), float(lon_values[1]))
    if not all(isfinite(value) for value in (*lat_bounds, *lon_bounds)):
        raise ValueError("bounding-box values must be finite")
    if not -90.0 <= lat_bounds[0] <= lat_bounds[1] <= 90.0:
        raise ValueError("latitude bounds must be ordered within [-90, 90]")
    if not -180.0 <= lon_bounds[0] <= lon_bounds[1] <= 180.0:
        raise ValueError("longitude bounds must be ordered within [-180, 180]")

    return lat_bounds, lon_bounds


def _component(vector: Mapping[str, float], name: str, index: int) -> float:
    try:
        value = vector[name]
    except KeyError as error:
        raise ValueError(f"vector {index} is missing component {name!r}") from error
    if not isfinite(value):
        raise ValueError(f"vector {index} component {name!r} must be finite")
    return value


def integrate_stochastic_trajectory(
    *,
    init_lat: float,
    init_lon: float,
    time_steps: Sequence[float],
    current_vectors: Sequence[Mapping[str, float]],
    wind_vectors: Sequence[Mapping[str, float]],
    diffusion_coefficients: Sequence[float],
    windage: float,
    prng: np.random.Generator,
    max_duration: float | None = None,
    bounding_box: Mapping[str, Sequence[float]] | None = None,
) -> StochasticTrajectoryResult:
    """Integrate deterministic advection and explicitly seeded diffusion."""
    step_count = len(time_steps)
    if (
        len(current_vectors) != step_count
        or len(wind_vectors) != step_count
        or len(diffusion_coefficients) != step_count
    ):
        raise ValueError(
            "dimension mismatch: time steps, current vectors, wind vectors, and "
            "diffusion coefficients must have identical lengths"
        )
    if max_duration is not None:
        if not isfinite(max_duration) or max_duration < 0.0:
            raise ValueError("max_duration must be finite and non-negative")

    bounds = _validated_bounds(bounding_box)
    baseline = compute_deterministic_step(
        lat=init_lat,
        lon=init_lon,
        u_current=0.0,
        v_current=0.0,
        u_wind=0.0,
        v_wind=0.0,
        windage=windage,
        dt=0.0,
    )
    current_lat = baseline["lat"]
    current_lon = baseline["lon"]
    elapsed_time = 0.0
    termination_reason = "completed"
    history = [
        StochasticTrajectoryPoint(
            step_index=0,
            elapsed_time=0.0,
            lat=current_lat,
            lon=current_lon,
            u_effective=0.0,
            v_effective=0.0,
            dx_stochastic_meters=0.0,
            dy_stochastic_meters=0.0,
        )
    ]

    for index, dt in enumerate(time_steps):
        if not isfinite(dt) or dt < 0.0:
            raise ValueError(f"time step {index} must be finite and non-negative")
        if max_duration is not None and elapsed_time + dt > max_duration:
            termination_reason = "max_duration_breach"
            break

        k_diffusion = diffusion_coefficients[index]
        if not isfinite(k_diffusion) or k_diffusion < 0.0:
            raise ValueError(
                f"diffusion coefficient {index} must be finite and non-negative"
            )

        current = current_vectors[index]
        wind = wind_vectors[index]
        deterministic = compute_deterministic_step(
            lat=current_lat,
            lon=current_lon,
            u_current=_component(current, "u", index),
            v_current=_component(current, "v", index),
            u_wind=_component(wind, "u", index),
            v_wind=_component(wind, "v", index),
            windage=windage,
            dt=dt,
        )
        stochastic = compute_stochastic_perturbation(
            lat=current_lat,
            k_diffusion=k_diffusion,
            dt=dt,
            prng=prng,
        )

        current_lat = deterministic["lat"] + stochastic.delta_lat
        if not -90.0 <= current_lat <= 90.0:
            raise ValueError("stochastic fusion produced latitude outside [-90, 90]")
        current_lon = (
            deterministic["lon"] + stochastic.delta_lon + 180.0
        ) % 360.0 - 180.0
        elapsed_time += dt
        history.append(
            StochasticTrajectoryPoint(
                step_index=index + 1,
                elapsed_time=elapsed_time,
                lat=current_lat,
                lon=current_lon,
                u_effective=deterministic["u_effective"],
                v_effective=deterministic["v_effective"],
                dx_stochastic_meters=stochastic.dx_meters,
                dy_stochastic_meters=stochastic.dy_meters,
            )
        )

        if bounds is not None:
            lat_bounds, lon_bounds = bounds
            inside_latitude = lat_bounds[0] <= current_lat <= lat_bounds[1]
            inside_longitude = lon_bounds[0] <= current_lon <= lon_bounds[1]
            if not inside_latitude or not inside_longitude:
                termination_reason = "spatial_boundary_breach"
                break

    return StochasticTrajectoryResult(
        final_lat=current_lat,
        final_lon=current_lon,
        total_elapsed_time=elapsed_time,
        termination_reason=termination_reason,
        trajectory_history=tuple(history),
    )
