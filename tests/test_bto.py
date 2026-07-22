import math

import pytest

from mh370_inverse_inference.satcom.bto import (
    bto_to_slant_range_m,
    refined_bto_to_satellite_aircraft_range_m,
    timing_error_to_range_m,
)
from mh370_inverse_inference.satcom.wgs84 import (
    ECEFPoint,
    ecef_distance_m,
)


def test_fifty_microseconds_round_trip_is_about_7_5_km() -> None:
    result = timing_error_to_range_m(50e-6)
    assert result == pytest.approx(7_494.81145, rel=1e-9)


def test_signed_timing_error_preserves_direction() -> None:
    assert timing_error_to_range_m(-50e-6) < 0


def test_one_way_conversion_does_not_divide_by_two() -> None:
    round_trip = timing_error_to_range_m(20e-6)
    one_way = timing_error_to_range_m(20e-6, round_trip=False)
    assert one_way == pytest.approx(round_trip * 2.0)


def test_absolute_bto_subtracts_explicit_calibration_delay() -> None:
    result = bto_to_slant_range_m(0.250, calibration_delay_s=0.010)
    expected = 299_792_458.0 * 0.240 / 2.0
    assert result == pytest.approx(expected)


def test_negative_corrected_bto_fails_closed() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        bto_to_slant_range_m(0.005, calibration_delay_s=0.010)


def test_non_finite_bto_fails_closed() -> None:
    with pytest.raises(ValueError, match="finite"):
        bto_to_slant_range_m(math.inf)


def test_refined_bto_selected_event_range_is_deterministic() -> None:
    satellite = ECEFPoint(
        x_m=18_178_354.27195026,
        y_m=38_050_848.06484729,
        z_m=393_043.6546171822,
    )
    perth_ges = ECEFPoint(
        x_m=-2_368_800.0,
        y_m=4_881_100.0,
        z_m=-3_342_000.0,
    )

    satellite_to_ges_range_m = ecef_distance_m(
        satellite,
        perth_ges,
    )

    assert satellite_to_ges_range_m == pytest.approx(
        39_196_534.11288632,
        abs=1e-6,
    )

    result = refined_bto_to_satellite_aircraft_range_m(
        18_400e-6,
        fixed_processing_bias_s=-495_679e-6,
        satellite_to_ges_range_m=satellite_to_ges_range_m,
    )

    assert result == pytest.approx(
        37_861_969.39520467,
        abs=1e-6,
    )


def test_refined_bto_rejects_negative_ges_range() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        refined_bto_to_satellite_aircraft_range_m(
            18_400e-6,
            fixed_processing_bias_s=-495_679e-6,
            satellite_to_ges_range_m=-1.0,
        )


def test_refined_bto_rejects_negative_derived_range() -> None:
    with pytest.raises(ValueError, match="Derived"):
        refined_bto_to_satellite_aircraft_range_m(
            18_400e-6,
            fixed_processing_bias_s=-495_679e-6,
            satellite_to_ges_range_m=100_000_000.0,
        )


def test_refined_bto_rejects_non_finite_input() -> None:
    with pytest.raises(ValueError, match="finite"):
        refined_bto_to_satellite_aircraft_range_m(
            math.inf,
            fixed_processing_bias_s=-495_679e-6,
            satellite_to_ges_range_m=39_196_534.0,
        )
