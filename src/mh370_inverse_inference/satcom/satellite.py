"""Validated satellite-position primitives for the L0.1 SATCOM layer."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    geodetic_to_ecef,
)


@dataclass(frozen=True, slots=True)
class SatellitePosition:
    """Immutable satellite position at one declared measurement epoch."""

    epoch_utc: str
    ecef: ECEFPoint

    def __post_init__(self) -> None:
        if type(self.epoch_utc) is not str:
            raise TypeError("epoch_utc must be str")
        if not self.epoch_utc.strip():
            raise ValueError("epoch_utc must not be empty")
        if type(self.ecef) is not ECEFPoint:
            raise TypeError("ecef must be ECEFPoint")
        if self.ecef.x_m == 0.0 and self.ecef.y_m == 0.0 and self.ecef.z_m == 0.0:
            raise ValueError("satellite position must not be the ECEF origin")

    @classmethod
    def from_geodetic(
        cls,
        *,
        epoch_utc: str,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float,
    ) -> SatellitePosition:
        """Construct a validated satellite position from WGS84 coordinates."""
        return cls(
            epoch_utc=epoch_utc,
            ecef=geodetic_to_ecef(
                GeodeticPoint(
                    latitude_deg=latitude_deg,
                    longitude_deg=longitude_deg,
                    altitude_m=altitude_m,
                )
            ),
        )


def _require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class ECEFVelocity:
    """Earth-centred, Earth-fixed Cartesian velocity in metres per second."""

    x_m_s: float
    y_m_s: float
    z_m_s: float

    def __post_init__(self) -> None:
        _require_finite(self.x_m_s, "x_m_s")
        _require_finite(self.y_m_s, "y_m_s")
        _require_finite(self.z_m_s, "z_m_s")


@dataclass(frozen=True, slots=True)
class SatelliteState:
    """Immutable satellite position and velocity at one declared epoch."""

    epoch_utc: str
    ecef: ECEFPoint
    velocity: ECEFVelocity

    def __post_init__(self) -> None:
        if type(self.epoch_utc) is not str:
            raise TypeError("epoch_utc must be str")
        if not self.epoch_utc.strip():
            raise ValueError("epoch_utc must not be empty")
        if type(self.ecef) is not ECEFPoint:
            raise TypeError("ecef must be ECEFPoint")
        if type(self.velocity) is not ECEFVelocity:
            raise TypeError("velocity must be ECEFVelocity")


def _hermite_position_component(
    *,
    start_position: float,
    start_velocity: float,
    end_position: float,
    end_velocity: float,
    duration_s: float,
    u: float,
) -> float:
    h00 = 2.0 * u**3 - 3.0 * u**2 + 1.0
    h10 = u**3 - 2.0 * u**2 + u
    h01 = -2.0 * u**3 + 3.0 * u**2
    h11 = u**3 - u**2

    return (
        h00 * start_position
        + h10 * duration_s * start_velocity
        + h01 * end_position
        + h11 * duration_s * end_velocity
    )


def _hermite_velocity_component(
    *,
    start_position: float,
    start_velocity: float,
    end_position: float,
    end_velocity: float,
    duration_s: float,
    u: float,
) -> float:
    dh00 = 6.0 * u**2 - 6.0 * u
    dh10 = 3.0 * u**2 - 4.0 * u + 1.0
    dh01 = -6.0 * u**2 + 6.0 * u
    dh11 = 3.0 * u**2 - 2.0 * u

    return (
        dh00 * start_position
        + dh10 * duration_s * start_velocity
        + dh01 * end_position
        + dh11 * duration_s * end_velocity
    ) / duration_s


def interpolate_satellite_state_cubic_hermite(
    *,
    epoch_utc: str,
    start_offset_s: float,
    target_offset_s: float,
    end_offset_s: float,
    start_position: ECEFPoint,
    start_velocity: ECEFVelocity,
    end_position: ECEFPoint,
    end_velocity: ECEFVelocity,
) -> SatelliteState:
    """Interpolate an ECEF state from endpoint positions and velocities."""

    for value, name in (
        (start_offset_s, "start_offset_s"),
        (target_offset_s, "target_offset_s"),
        (end_offset_s, "end_offset_s"),
    ):
        _require_finite(value, name)

    if end_offset_s <= start_offset_s:
        raise ValueError("end_offset_s must be greater than start_offset_s")
    if not start_offset_s <= target_offset_s <= end_offset_s:
        raise ValueError("target_offset_s must be within the interpolation interval")

    duration_s = end_offset_s - start_offset_s
    u = (target_offset_s - start_offset_s) / duration_s

    position = ECEFPoint(
        x_m=_hermite_position_component(
            start_position=start_position.x_m,
            start_velocity=start_velocity.x_m_s,
            end_position=end_position.x_m,
            end_velocity=end_velocity.x_m_s,
            duration_s=duration_s,
            u=u,
        ),
        y_m=_hermite_position_component(
            start_position=start_position.y_m,
            start_velocity=start_velocity.y_m_s,
            end_position=end_position.y_m,
            end_velocity=end_velocity.y_m_s,
            duration_s=duration_s,
            u=u,
        ),
        z_m=_hermite_position_component(
            start_position=start_position.z_m,
            start_velocity=start_velocity.z_m_s,
            end_position=end_position.z_m,
            end_velocity=end_velocity.z_m_s,
            duration_s=duration_s,
            u=u,
        ),
    )

    velocity = ECEFVelocity(
        x_m_s=_hermite_velocity_component(
            start_position=start_position.x_m,
            start_velocity=start_velocity.x_m_s,
            end_position=end_position.x_m,
            end_velocity=end_velocity.x_m_s,
            duration_s=duration_s,
            u=u,
        ),
        y_m_s=_hermite_velocity_component(
            start_position=start_position.y_m,
            start_velocity=start_velocity.y_m_s,
            end_position=end_position.y_m,
            end_velocity=end_velocity.y_m_s,
            duration_s=duration_s,
            u=u,
        ),
        z_m_s=_hermite_velocity_component(
            start_position=start_position.z_m,
            start_velocity=start_velocity.z_m_s,
            end_position=end_position.z_m,
            end_velocity=end_velocity.z_m_s,
            duration_s=duration_s,
            u=u,
        ),
    )

    return SatelliteState(
        epoch_utc=epoch_utc,
        ecef=position,
        velocity=velocity,
    )
