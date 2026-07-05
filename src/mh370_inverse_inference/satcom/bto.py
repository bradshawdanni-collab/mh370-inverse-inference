"""Burst Timing Offset helpers.

The functions in this module are deliberately small and deterministic. They do not
infer an aircraft location; they only implement auditable measurement conversions.
"""

from math import isfinite

SPEED_OF_LIGHT_M_S: float = 299_792_458.0


def timing_error_to_range_m(
    timing_error_s: float,
    *,
    round_trip: bool = True,
) -> float:
    """Convert a timing error in seconds to a path-length error in metres.

    Args:
        timing_error_s: Timing error in seconds. May be signed.
        round_trip: Divide by two for a round-trip timing measurement such as BTO.

    Returns:
        Signed range error in metres.
    """
    if not isfinite(timing_error_s):
        raise ValueError("timing_error_s must be finite")
    divisor = 2.0 if round_trip else 1.0
    return SPEED_OF_LIGHT_M_S * timing_error_s / divisor


def bto_to_slant_range_m(
    bto_s: float,
    *,
    calibration_delay_s: float = 0.0,
) -> float:
    """Convert calibrated round-trip BTO timing into one-way slant range.

    The caller must supply any equipment, terminal, or processing delay explicitly.
    No historical calibration constant is embedded in this function.
    """
    if not all(isfinite(value) for value in (bto_s, calibration_delay_s)):
        raise ValueError("BTO inputs must be finite")

    corrected_round_trip_s = bto_s - calibration_delay_s
    if corrected_round_trip_s < 0.0:
        raise ValueError("Corrected BTO timing must be non-negative")

    return timing_error_to_range_m(corrected_round_trip_s, round_trip=True)
