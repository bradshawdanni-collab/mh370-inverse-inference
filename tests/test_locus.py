from mh370_inverse_inference.satcom.geometry import slant_range_m
from mh370_inverse_inference.satcom.locus import generate_slant_range_locus
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint, geodetic_to_ecef


def test_locus_generation_is_deterministic_and_ordered() -> None:
    satellite = geodetic_to_ecef(
        GeodeticPoint(latitude_deg=0.0, longitude_deg=64.5, altitude_m=35_786_000.0)
    )
    reference = GeodeticPoint(latitude_deg=-30.0, longitude_deg=90.0)
    target_range_m = slant_range_m(geodetic_to_ecef(reference), satellite)

    first = generate_slant_range_locus(
        satellite_ecef=satellite,
        target_range_m=target_range_m,
        range_uncertainty_m=7_500.0,
        longitude_step_deg=30.0,
        latitude_step_deg=2.0,
        tolerance_m=10.0,
    )
    second = generate_slant_range_locus(
        satellite_ecef=satellite,
        target_range_m=target_range_m,
        range_uncertainty_m=7_500.0,
        longitude_step_deg=30.0,
        latitude_step_deg=2.0,
        tolerance_m=10.0,
    )

    assert first == second
    assert first.nominal
    assert first.lower
    assert first.upper


def test_negative_uncertainty_is_rejected() -> None:
    satellite = geodetic_to_ecef(
        GeodeticPoint(latitude_deg=0.0, longitude_deg=64.5, altitude_m=35_786_000.0)
    )
    reference = GeodeticPoint(latitude_deg=-30.0, longitude_deg=90.0)
    target_range_m = slant_range_m(geodetic_to_ecef(reference), satellite)

    try:
        generate_slant_range_locus(
            satellite_ecef=satellite,
            target_range_m=target_range_m,
            range_uncertainty_m=-1.0,
        )
    except ValueError:
        return
    raise AssertionError("negative uncertainty was accepted")
