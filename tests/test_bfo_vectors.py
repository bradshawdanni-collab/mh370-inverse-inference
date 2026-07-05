"""Tests for L2 BFO vector geometry and sign conventions."""

import math

import pytest

from mh370_inverse_inference.satcom.bfo import (
    ECEFVelocity,
    one_way_doppler_hz,
    range_rate_mps,
    unit_line_of_sight,
)
from mh370_inverse_inference.satcom.wgs84 import ECEFPoint


def test_unit_line_of_sight_points_from_transmitter_to_receiver() -> None:
    direction = unit_line_of_sight(
        ECEFPoint(x_m=0.0, y_m=0.0, z_m=0.0),
        ECEFPoint(x_m=3.0, y_m=4.0, z_m=0.0),
    )

    assert direction == pytest.approx((0.6, 0.8, 0.0))


def test_zero_relative_radial_velocity_produces_zero_doppler() -> None:
    rate = range_rate_mps(
        transmitter_position=ECEFPoint(0.0, 0.0, 0.0),
        receiver_position=ECEFPoint(1_000.0, 0.0, 0.0),
        transmitter_velocity=ECEFVelocity(50.0, 0.0, 0.0),
        receiver_velocity=ECEFVelocity(50.0, 0.0, 0.0),
    )

    assert rate == 0.0
    assert one_way_doppler_hz(carrier_hz=1.0e9, range_rate_mps_value=rate) == 0.0


def test_separating_motion_produces_negative_doppler() -> None:
    rate = range_rate_mps(
        transmitter_position=ECEFPoint(0.0, 0.0, 0.0),
        receiver_position=ECEFPoint(1_000.0, 0.0, 0.0),
        transmitter_velocity=ECEFVelocity(0.0, 0.0, 0.0),
        receiver_velocity=ECEFVelocity(100.0, 0.0, 0.0),
    )

    assert rate == 100.0
    assert one_way_doppler_hz(
        carrier_hz=1.0e9, range_rate_mps_value=rate
    ) < 0.0


def test_closing_motion_produces_positive_doppler() -> None:
    rate = range_rate_mps(
        transmitter_position=ECEFPoint(0.0, 0.0, 0.0),
        receiver_position=ECEFPoint(1_000.0, 0.0, 0.0),
        transmitter_velocity=ECEFVelocity(0.0, 0.0, 0.0),
        receiver_velocity=ECEFVelocity(-100.0, 0.0, 0.0),
    )

    assert rate == -100.0
    assert one_way_doppler_hz(
        carrier_hz=1.0e9, range_rate_mps_value=rate
    ) > 0.0


def test_coincident_positions_fail_closed() -> None:
    point = ECEFPoint(1.0, 2.0, 3.0)
    with pytest.raises(ValueError, match="coincident"):
        unit_line_of_sight(point, point)


def test_invalid_carrier_fails_closed() -> None:
    with pytest.raises(ValueError, match="Carrier frequency"):
        one_way_doppler_hz(carrier_hz=0.0, range_rate_mps_value=10.0)


def test_velocity_requires_finite_components() -> None:
    with pytest.raises(ValueError, match="finite"):
        ECEFVelocity(math.inf, 0.0, 0.0)
