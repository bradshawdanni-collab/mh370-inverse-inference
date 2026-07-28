"""Deterministic published-BTO to WGS84 zero-height transformations."""

from __future__ import annotations

import math

from mh370_inverse_inference.satcom.bto import SPEED_OF_LIGHT_M_S
from mh370_inverse_inference.satcom.locus import SurfaceLocusResult, generate_surface_locus
from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.wgs84 import ECEFPoint, ecef_distance_m


def _require_finite_real(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def published_bto_aircraft_range_m(
    *,
    corrected_bto_microseconds: float,
    fixed_processing_bias_microseconds: float,
    satellite: SatellitePosition,
    perth_ges_ecef: ECEFPoint,
) -> float:
    """Derive satellite-to-aircraft range from the frozen published BTO model.

    Implements the declared relation::

        rho_aircraft = c * (BTO - bias) / 2 - rho_satellite_to_GES

    where BTO and bias are supplied in microseconds and the geometry is ECEF.
    """

    _require_finite_real(corrected_bto_microseconds, "corrected_bto_microseconds")
    _require_finite_real(
        fixed_processing_bias_microseconds,
        "fixed_processing_bias_microseconds",
    )
    if corrected_bto_microseconds < 0.0:
        raise ValueError("corrected_bto_microseconds must be non-negative")
    if type(satellite) is not SatellitePosition:
        raise TypeError("satellite must be SatellitePosition")
    if type(perth_ges_ecef) is not ECEFPoint:
        raise TypeError("perth_ges_ecef must be ECEFPoint")

    bto_timing_s = (
        corrected_bto_microseconds - fixed_processing_bias_microseconds
    ) * 1e-6
    if bto_timing_s <= 0.0:
        raise ValueError("BTO minus processing bias must be positive")

    bto_half_path_m = SPEED_OF_LIGHT_M_S * bto_timing_s / 2.0
    satellite_to_ges_range_m = ecef_distance_m(satellite.ecef, perth_ges_ecef)
    aircraft_range_m = bto_half_path_m - satellite_to_ges_range_m
    if aircraft_range_m <= 0.0:
        raise ValueError("derived satellite-to-aircraft range must be positive")
    return aircraft_range_m


def generate_published_bto_zero_height_locus(
    *,
    corrected_bto_microseconds: float,
    fixed_processing_bias_microseconds: float,
    satellite: SatellitePosition,
    perth_ges_ecef: ECEFPoint,
    tolerance_m: float = 1.0,
    longitude_step_deg: float = 1.0,
    latitude_step_deg: float = 1.0,
    minimum_longitude_deg: float = -180.0,
    maximum_longitude_deg: float = 180.0,
    minimum_latitude_deg: float = -90.0,
    maximum_latitude_deg: float = 90.0,
    maximum_iterations: int = 64,
) -> SurfaceLocusResult:
    """Generate a deterministic WGS84 zero-height locus from frozen BTO inputs."""

    target_range_m = published_bto_aircraft_range_m(
        corrected_bto_microseconds=corrected_bto_microseconds,
        fixed_processing_bias_microseconds=fixed_processing_bias_microseconds,
        satellite=satellite,
        perth_ges_ecef=perth_ges_ecef,
    )
    return generate_surface_locus(
        satellite,
        target_range_m,
        tolerance_m=tolerance_m,
        longitude_step_deg=longitude_step_deg,
        latitude_step_deg=latitude_step_deg,
        minimum_longitude_deg=minimum_longitude_deg,
        maximum_longitude_deg=maximum_longitude_deg,
        minimum_latitude_deg=minimum_latitude_deg,
        maximum_latitude_deg=maximum_latitude_deg,
        maximum_iterations=maximum_iterations,
    )
