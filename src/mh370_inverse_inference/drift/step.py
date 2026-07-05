"""Deterministic single-step displacement for ocean-drift trajectories."""

from math import cos, degrees, isfinite, radians
from typing import TypedDict

EARTH_RADIUS_M = 6_371_000.0
_POLAR_COSINE_LIMIT = 1e-12


class DriftStepResult(TypedDict):
    """Geographic position and effective velocity after one drift step."""

    lat: float
    lon: float
    u_effective: float
    v_effective: float


def compute_deterministic_step(
    *,
    lat: float,
    lon: float,
    u_current: float,
    v_current: float,
    u_wind: float,
    v_wind: float,
    windage: float,
    dt: float,
) -> DriftStepResult:
    """Advance one forward-Euler step using current and windage-scaled wind.

    Eastward and northward effective velocities are calculated in metres per
    second. The resulting linear displacement is translated to latitude and
    longitude using a spherical-Earth approximation.
    """
    values = (
        lat,
        lon,
        u_current,
        v_current,
        u_wind,
        v_wind,
        windage,
        dt,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("all drift-step inputs must be finite")
    if not -90.0 <= lat <= 90.0:
        raise ValueError("latitude must be within [-90, 90]")
    if windage < 0.0:
        raise ValueError("windage must be non-negative")
    if dt < 0.0:
        raise ValueError("dt must be non-negative")

    latitude_radians = radians(lat)
    latitude_scale = cos(latitude_radians)
    if abs(latitude_scale) < _POLAR_COSINE_LIMIT and dt != 0.0:
        raise ValueError("longitude displacement is undefined at the poles")

    u_effective = u_current + windage * u_wind
    v_effective = v_current + windage * v_wind

    delta_latitude = degrees(v_effective * dt / EARTH_RADIUS_M)
    delta_longitude = 0.0
    if dt != 0.0:
        delta_longitude = degrees(u_effective * dt / (EARTH_RADIUS_M * latitude_scale))

    new_longitude = (lon + delta_longitude + 180.0) % 360.0 - 180.0

    return {
        "lat": lat + delta_latitude,
        "lon": new_longitude,
        "u_effective": u_effective,
        "v_effective": v_effective,
    }
