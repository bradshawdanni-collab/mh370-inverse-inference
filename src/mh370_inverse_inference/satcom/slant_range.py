"""Deterministic geometric range calculations."""

from __future__ import annotations

from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.wgs84 import ECEFPoint, ecef_distance_m


def slant_range_m(point: ECEFPoint, satellite: SatellitePosition) -> float:
    """Return the straight-line distance from an ECEF point to a satellite."""
    if type(point) is not ECEFPoint:
        raise TypeError("point must be ECEFPoint")
    if type(satellite) is not SatellitePosition:
        raise TypeError("satellite must be SatellitePosition")
    return ecef_distance_m(point, satellite.ecef)
