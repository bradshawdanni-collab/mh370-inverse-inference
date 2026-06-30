import pytest

from mh370_inverse_inference.satcom.arc import (
    generate_arc_band,
    generate_geodesic_circle,
)
from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


def test_geodesic_circle_is_closed_and_has_expected_radius() -> None:
    center = GeodeticPoint(latitude_deg=-34.0, longitude_deg=93.0)
    points = generate_geodesic_circle(center, radius_m=100_000.0, point_count=12)

    assert len(points) == 13
    assert points[0] == points[-1]
    for point in points[:-1]:
        assert geodesic_distance_m(center, point) == pytest.approx(
            100_000.0,
            abs=0.01,
        )


def test_arc_band_orders_boundaries() -> None:
    center = GeodeticPoint(latitude_deg=-34.0, longitude_deg=93.0)
    band = generate_arc_band(
        center,
        nominal_radius_m=1_000_000.0,
        radial_uncertainty_m=10_000.0,
        point_count=8,
    )

    lower_distance = geodesic_distance_m(center, band.lower[0])
    nominal_distance = geodesic_distance_m(center, band.nominal[0])
    upper_distance = geodesic_distance_m(center, band.upper[0])

    assert lower_distance == pytest.approx(990_000.0, abs=0.01)
    assert nominal_distance == pytest.approx(1_000_000.0, abs=0.01)
    assert upper_distance == pytest.approx(1_010_000.0, abs=0.01)


def test_invalid_circle_arguments_are_rejected() -> None:
    center = GeodeticPoint(latitude_deg=0.0, longitude_deg=0.0)
    with pytest.raises(ValueError):
        generate_geodesic_circle(center, radius_m=-1.0)
    with pytest.raises(ValueError):
        generate_geodesic_circle(center, radius_m=1.0, point_count=3)
