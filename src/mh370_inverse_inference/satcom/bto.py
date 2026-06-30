"""Burst Timing Offset helpers.

The functions in this module are deliberately small and deterministic. They do not
infer an aircraft location; they only implement auditable measurement conversions.
"""

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
    divisor = 2.0 if round_trip else 1.0
    return SPEED_OF_LIGHT_M_S * timing_error_s / divisor
