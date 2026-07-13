"""Validated satellite-position primitives for the L0.1 SATCOM layer."""

from __future__ import annotations

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
