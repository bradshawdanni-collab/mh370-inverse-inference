"""SATCOM geometry and measurement models."""

from mh370_inverse_inference.satcom.bto import (
    SPEED_OF_LIGHT_M_S,
    timing_error_to_range_m,
)
from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.slant_range import slant_range_m
from mh370_inverse_inference.satcom.wgs84 import (
    WGS84_A_M,
    WGS84_B_M,
    WGS84_E2,
    WGS84_EP2,
    WGS84_F,
    ECEFPoint,
    GeodeticPoint,
    ecef_distance_m,
    ecef_to_geodetic,
    geodetic_to_ecef,
    normalize_longitude_deg,
)

__all__ = [
    "ECEFPoint",
    "GeodeticPoint",
    "SPEED_OF_LIGHT_M_S",
    "SatellitePosition",
    "WGS84_A_M",
    "WGS84_B_M",
    "WGS84_E2",
    "WGS84_EP2",
    "WGS84_F",
    "ecef_distance_m",
    "ecef_to_geodetic",
    "geodetic_to_ecef",
    "normalize_longitude_deg",
    "slant_range_m",
    "timing_error_to_range_m",
]
