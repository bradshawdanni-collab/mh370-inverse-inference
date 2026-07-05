"""Tests for L2 BFO composition, inversion, and residuals."""

import pytest

from mh370_inverse_inference.satcom.bfo import (
    ECEFVelocity,
    bfo_residual_hz,
    invert_aircraft_los_velocity_mps,
    invert_downlink_range_rate_mps,
    predict_two_leg_bfo,
)
from mh370_inverse_inference.satcom.wgs84 import ECEFPoint


def test_forward_calculation_then_inversion_recovers_range_rate() -> None:
    ground = ECEFPoint(0.0, 0.0, 0.0)
    satellite = ECEFPoint(10_000.0, 0.0, 0.0)
    aircraft = ECEFPoint(20_000.0, 0.0, 0.0)
    ground_velocity = ECEFVelocity(0.0, 0.0, 0.0)
    satellite_velocity = ECEFVelocity(10.0, 0.0, 0.0)
    aircraft_velocity = ECEFVelocity(110.0, 0.0, 0.0)

    components = predict_two_leg_bfo(
        ground_position=ground,
        satellite_position=satellite,
        aircraft_position=aircraft,
        ground_velocity=ground_velocity,
        satellite_velocity=satellite_velocity,
        aircraft_velocity=aircraft_velocity,
        uplink_carrier_hz=1.6e9,
        downlink_carrier_hz=1.5e9,
        bias_hz=12.0,
    )

    recovered = invert_downlink_range_rate_mps(
        observed_bfo_hz=components.total_hz,
        uplink_doppler_hz=components.uplink_hz,
        bias_hz=components.bias_hz,
        downlink_carrier_hz=1.5e9,
    )

    assert recovered == pytest.approx(100.0)


def test_aircraft_los_inversion_restores_aircraft_component() -> None:
    satellite = ECEFPoint(10_000.0, 0.0, 0.0)
    aircraft = ECEFPoint(20_000.0, 0.0, 0.0)
    satellite_velocity = ECEFVelocity(10.0, 0.0, 0.0)

    aircraft_component = invert_aircraft_los_velocity_mps(
        observed_bfo_hz=-500.3461427972281,
        uplink_doppler_hz=0.0,
        bias_hz=0.0,
        downlink_carrier_hz=1.5e9,
        satellite_position=satellite,
        aircraft_position=aircraft,
        satellite_velocity=satellite_velocity,
    )

    assert aircraft_component == pytest.approx(110.0)


def test_two_leg_components_remain_separately_inspectable() -> None:
    components = predict_two_leg_bfo(
        ground_position=ECEFPoint(0.0, 0.0, 0.0),
        satellite_position=ECEFPoint(10_000.0, 0.0, 0.0),
        aircraft_position=ECEFPoint(20_000.0, 0.0, 0.0),
        ground_velocity=ECEFVelocity(0.0, 0.0, 0.0),
        satellite_velocity=ECEFVelocity(10.0, 0.0, 0.0),
        aircraft_velocity=ECEFVelocity(110.0, 0.0, 0.0),
        uplink_carrier_hz=1.6e9,
        downlink_carrier_hz=1.5e9,
        bias_hz=12.0,
    )

    assert components.uplink_hz < 0.0
    assert components.downlink_hz < 0.0
    assert components.bias_hz == 12.0
    assert components.total_hz == pytest.approx(
        components.uplink_hz + components.downlink_hz + components.bias_hz
    )


def test_residual_is_observed_minus_predicted() -> None:
    assert bfo_residual_hz(observed_bfo_hz=25.0, predicted_bfo_hz=20.0) == 5.0
