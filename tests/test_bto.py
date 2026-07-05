import math

import pytest

from mh370_inverse_inference.satcom.bto import (
    bto_to_slant_range_m,
    timing_error_to_range_m,
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
