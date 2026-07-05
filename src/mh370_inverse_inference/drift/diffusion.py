"""Explicit-PRNG stochastic diffusion for ocean-drift trajectories."""

from dataclasses import dataclass
from math import cos, degrees, isfinite, radians, sqrt

import numpy as np

from mh370_inverse_inference.drift.step import EARTH_RADIUS_M

_POLAR_COSINE_LIMIT = 1e-12


@dataclass(frozen=True, slots=True)
class DiffusionPerturbation:
    """Immutable stochastic geographic displacement."""

    delta_lat: float
    delta_lon: float
    dx_meters: float
    dy_meters: float


def compute_stochastic_perturbation(
    *,
    lat: float,
    k_diffusion: float,
    dt: float,
    prng: np.random.Generator,
) -> DiffusionPerturbation:
    """Sample one isotropic diffusion perturbation using injected PRNG state.

    Each horizontal displacement component is sampled independently from a
    zero-mean normal distribution with variance ``2 * k_diffusion * dt``.
    """
    if not all(isfinite(value) for value in (lat, k_diffusion, dt)):
        raise ValueError("diffusion inputs must be finite")
    if not -90.0 <= lat <= 90.0:
        raise ValueError("latitude must be within [-90, 90]")
    if k_diffusion < 0.0:
        raise ValueError("diffusion coefficient must be non-negative")
    if dt < 0.0:
        raise ValueError("dt must be non-negative")

    if k_diffusion == 0.0 or dt == 0.0:
        return DiffusionPerturbation(
            delta_lat=0.0,
            delta_lon=0.0,
            dx_meters=0.0,
            dy_meters=0.0,
        )

    latitude_scale = cos(radians(lat))
    if abs(latitude_scale) < _POLAR_COSINE_LIMIT:
        raise ValueError("longitude perturbation is undefined at the poles")

    sigma_meters = sqrt(2.0 * k_diffusion * dt)
    dx_meters = float(prng.normal(loc=0.0, scale=sigma_meters))
    dy_meters = float(prng.normal(loc=0.0, scale=sigma_meters))

    return DiffusionPerturbation(
        delta_lat=degrees(dy_meters / EARTH_RADIUS_M),
        delta_lon=degrees(dx_meters / (EARTH_RADIUS_M * latitude_scale)),
        dx_meters=dx_meters,
        dy_meters=dy_meters,
    )
