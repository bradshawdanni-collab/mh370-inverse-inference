from mh370_inverse_inference.satcom.bto import timing_error_to_range_m


def test_fifty_microseconds_round_trip_is_about_7_5_km() -> None:
    result = timing_error_to_range_m(50e-6)
    assert result == pytest.approx(7_494.81145, rel=1e-9)


def test_signed_timing_error_preserves_direction() -> None:
    assert timing_error_to_range_m(-50e-6) < 0


def test_one_way_conversion_does_not_divide_by_two() -> None:
    round_trip = timing_error_to_range_m(20e-6)
    one_way = timing_error_to_range_m(20e-6, round_trip=False)
    assert one_way == pytest.approx(round_trip * 2.0)


import pytest
