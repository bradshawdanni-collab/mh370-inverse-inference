"""Deterministic Doppler primitives for Burst Frequency Offset analysis."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

from mh370_inverse_inference.satcom.wgs84 import ECEFPoint

SPEED_OF_LIGHT_MPS: float = 299_792_458.0


@dataclass(frozen=True, slots=True)
class ECEFVelocity:
    """Earth-centred, Earth-fixed Cartesian velocity in metres/second."""

    x_mps: float
    y_mps: float
    z_mps: float

    def __post_init__(self) -> None:
        if not all(isfinite(value) for value in self.as_tuple()):
            raise ValueError("ECEF velocity components must be finite")

    def as_tuple(self) -> tuple[float, float, float]:
        """Return components as an immutable tuple."""
        return self.x_mps, self.y_mps, self.z_mps


@dataclass(frozen=True, slots=True)
class DopplerComponents:
    """Inspectable terms contributing to a predicted BFO value."""

    uplink_hz: float
    downlink_hz: float
    bias_hz: float

    def __post_init__(self) -> None:
        if not all(
            isfinite(value)
            for value in (self.uplink_hz, self.downlink_hz, self.bias_hz)
        ):
            raise ValueError("Doppler components must be finite")

    @property
    def total_hz(self) -> float:
        """Return the composed predicted BFO."""
        return self.uplink_hz + self.downlink_hz + self.bias_hz


def _validate_carrier_hz(carrier_hz: float) -> None:
    if not isfinite(carrier_hz) or carrier_hz <= 0.0:
        raise ValueError("Carrier frequency must be finite and positive")


def unit_line_of_sight(
    transmitter: ECEFPoint, receiver: ECEFPoint
) -> tuple[float, float, float]:
    """Return the unit vector pointing from transmitter to receiver."""
    dx = receiver.x_m - transmitter.x_m
    dy = receiver.y_m - transmitter.y_m
    dz = receiver.z_m - transmitter.z_m
    magnitude = sqrt(dx * dx + dy * dy + dz * dz)
    if magnitude == 0.0:
        raise ValueError("Line of sight is undefined for coincident positions")
    return dx / magnitude, dy / magnitude, dz / magnitude


def dot_velocity(
    velocity: ECEFVelocity, direction: tuple[float, float, float]
) -> float:
    """Project an ECEF velocity onto a direction vector."""
    return (
        velocity.x_mps * direction[0]
        + velocity.y_mps * direction[1]
        + velocity.z_mps * direction[2]
    )


def range_rate_mps(
    *,
    transmitter_position: ECEFPoint,
    receiver_position: ECEFPoint,
    transmitter_velocity: ECEFVelocity,
    receiver_velocity: ECEFVelocity,
) -> float:
    """Return signed transmitter-receiver separation rate.

    Positive values mean increasing range. Negative values mean closing range.
    """
    line_of_sight = unit_line_of_sight(transmitter_position, receiver_position)
    relative_velocity = ECEFVelocity(
        x_mps=receiver_velocity.x_mps - transmitter_velocity.x_mps,
        y_mps=receiver_velocity.y_mps - transmitter_velocity.y_mps,
        z_mps=receiver_velocity.z_mps - transmitter_velocity.z_mps,
    )
    return dot_velocity(relative_velocity, line_of_sight)


def one_way_doppler_hz(*, carrier_hz: float, range_rate_mps_value: float) -> float:
    """Return classical one-way Doppler shift for a signed range rate."""
    _validate_carrier_hz(carrier_hz)
    if not isfinite(range_rate_mps_value):
        raise ValueError("Range rate must be finite")
    return -(carrier_hz / SPEED_OF_LIGHT_MPS) * range_rate_mps_value


def predict_two_leg_bfo(
    *,
    ground_position: ECEFPoint,
    satellite_position: ECEFPoint,
    aircraft_position: ECEFPoint,
    ground_velocity: ECEFVelocity,
    satellite_velocity: ECEFVelocity,
    aircraft_velocity: ECEFVelocity,
    uplink_carrier_hz: float,
    downlink_carrier_hz: float,
    bias_hz: float = 0.0,
) -> DopplerComponents:
    """Compose ground-satellite and satellite-aircraft Doppler terms."""
    if not isfinite(bias_hz):
        raise ValueError("Bias must be finite")

    uplink_rate = range_rate_mps(
        transmitter_position=ground_position,
        receiver_position=satellite_position,
        transmitter_velocity=ground_velocity,
        receiver_velocity=satellite_velocity,
    )
    downlink_rate = range_rate_mps(
        transmitter_position=satellite_position,
        receiver_position=aircraft_position,
        transmitter_velocity=satellite_velocity,
        receiver_velocity=aircraft_velocity,
    )
    return DopplerComponents(
        uplink_hz=one_way_doppler_hz(
            carrier_hz=uplink_carrier_hz,
            range_rate_mps_value=uplink_rate,
        ),
        downlink_hz=one_way_doppler_hz(
            carrier_hz=downlink_carrier_hz,
            range_rate_mps_value=downlink_rate,
        ),
        bias_hz=bias_hz,
    )


def invert_downlink_range_rate_mps(
    *,
    observed_bfo_hz: float,
    uplink_doppler_hz: float,
    bias_hz: float,
    downlink_carrier_hz: float,
) -> float:
    """Recover required satellite-aircraft range rate from an observed BFO."""
    _validate_carrier_hz(downlink_carrier_hz)
    if not all(
        isfinite(value)
        for value in (observed_bfo_hz, uplink_doppler_hz, bias_hz)
    ):
        raise ValueError("BFO inversion inputs must be finite")

    downlink_doppler_hz = observed_bfo_hz - uplink_doppler_hz - bias_hz
    return -(SPEED_OF_LIGHT_MPS / downlink_carrier_hz) * downlink_doppler_hz


def invert_aircraft_los_velocity_mps(
    *,
    observed_bfo_hz: float,
    uplink_doppler_hz: float,
    bias_hz: float,
    downlink_carrier_hz: float,
    satellite_position: ECEFPoint,
    aircraft_position: ECEFPoint,
    satellite_velocity: ECEFVelocity,
) -> float:
    """Recover the aircraft velocity component along satellite-to-aircraft LOS."""
    line_of_sight = unit_line_of_sight(satellite_position, aircraft_position)
    required_range_rate = invert_downlink_range_rate_mps(
        observed_bfo_hz=observed_bfo_hz,
        uplink_doppler_hz=uplink_doppler_hz,
        bias_hz=bias_hz,
        downlink_carrier_hz=downlink_carrier_hz,
    )
    satellite_los_velocity = dot_velocity(satellite_velocity, line_of_sight)
    return required_range_rate + satellite_los_velocity


def bfo_residual_hz(*, observed_bfo_hz: float, predicted_bfo_hz: float) -> float:
    """Return observed minus predicted BFO in hertz."""
    if not all(isfinite(value) for value in (observed_bfo_hz, predicted_bfo_hz)):
        raise ValueError("BFO residual inputs must be finite")
    return observed_bfo_hz - predicted_bfo_hz
