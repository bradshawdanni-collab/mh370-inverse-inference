"""Satellite position representation for SATCOM geometry."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.satcom.wgs84 import ECEFPoint, GeodeticPoint, geodetic_to_ecef


@dataclass(frozen=True, slots=True)
class SatellitePosition:
    """Satellite position at one measurement epoch."""

    epoch_utc: str
    ecef: ECEFPoint

    @classmethod
    def from_geodetic(
        cls,
        *,
        epoch_utc: str,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float,
    ) -> SatellitePosition:
        """Construct a satellite position from WGS84 geodetic coordinates."""
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
