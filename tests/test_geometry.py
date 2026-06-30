import pytest

from mh370_inverse_inference.satcom.geometry import (
    geodesic_distance_m,
    slant_range_m,
)
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    GeodeticPoint,
    ecef_to_geodetic,
    geodetic_to_ecef,
)


def test_geodetic_ecef_round_trip() -> None:
    original = GeodeticPoint(
        latitude_deg=-34.0,
        longitude_deg=93.0,
        altitude_m=10_000.0,
    )
    recovered = ecef_to_geodetic(geodetic_to_ecef(original))

    assert recovered.latitude_deg == pytest.approx(original.latitude_deg, abs=1e-8)
    assert recovered.longitude_deg == pytest.approx(original.longitude_deg, abs=1e-8)
    assert recovered.altitude_m == pytest.approx(original.altitude_m, abs=1e-4)


def test_slant_range_uses_ecef_distance() -> None:
    first = ECEFPoint(0.0, 0.0, 0.0)
    second = ECEFPoint(3.0, 4.0, 12.0)
    assert slant_range_m(first, second) == pytest.approx(13.0)


def test_wgs84_equatorial_degree_distance() -> None:
    first = GeodeticPoint(latitude_deg=0.0, longitude_deg=0.0)
    second = GeodeticPoint(latitude_deg=0.0, longitude_deg=1.0)
    assert geodesic_distance_m(first, second) == pytest.approx(111_319.49, rel=1e-6)
