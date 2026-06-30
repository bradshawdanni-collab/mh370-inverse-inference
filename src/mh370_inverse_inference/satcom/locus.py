"""Deterministic BTO slant-range locus generation."""

from __future__ import annotations

from dataclasses import dataclass

from mh370_inverse_inference.satcom.intersection import solve_latitudes_for_longitude
from mh370_inverse_inference.satcom.wgs84 import ECEFPoint, GeodeticPoint


@dataclass(frozen=True, slots=True)
class SlantRangeLocus:
    """Nominal and uncertainty-bound Earth-surface loci."""

    nominal: tuple[GeodeticPoint, ...]
    lower: tuple[GeodeticPoint, ...]
    upper: tuple[GeodeticPoint, ...]


def generate_slant_range_locus(
    *,
    satellite_ecef: ECEFPoint,
    target_range_m: float,
    range_uncertainty_m: float,
    altitude_m: float = 0.0,
    longitude_step_deg: float = 1.0,
    latitude_step_deg: float = 1.0,
    tolerance_m: float = 1.0,
) -> SlantRangeLocus:
    """Generate nominal/lower/upper WGS84 loci by longitude scanning."""
    if range_uncertainty_m < 0.0:
        raise ValueError("range_uncertainty_m must be non-negative")
    if longitude_step_deg <= 0.0 or longitude_step_deg > 30.0:
        raise ValueError("longitude_step_deg must be in (0, 30]")

    def build(range_m: float) -> tuple[GeodeticPoint, ...]:
        points: list[GeodeticPoint] = []
        longitude = -180.0
        while longitude < 180.0:
            roots = solve_latitudes_for_longitude(
                longitude_deg=longitude,
                satellite_ecef=satellite_ecef,
                target_range_m=range_m,
                altitude_m=altitude_m,
                latitude_step_deg=latitude_step_deg,
                tolerance_m=tolerance_m,
            )
            points.extend(
                GeodeticPoint(root.latitude_deg, root.longitude_deg, altitude_m)
                for root in roots
            )
            longitude += longitude_step_deg
        return tuple(points)

    lower_range = max(1.0, target_range_m - range_uncertainty_m)
    upper_range = target_range_m + range_uncertainty_m
    return SlantRangeLocus(
        nominal=build(target_range_m),
        lower=build(lower_range),
        upper=build(upper_range),
    )
