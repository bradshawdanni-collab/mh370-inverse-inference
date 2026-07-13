"""Tests for deterministic SATCOM slant-range uncertainty bands."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.satcom.satellite import SatellitePosition
from mh370_inverse_inference.satcom.uncertainty import (
    SlantRangeBand,
    SlantRangeUncertainty,
    SlantRangeUncertaintyBands,
    generate_uncertainty_bands,
)


def _satellite() -> SatellitePosition:
    return SatellitePosition.from_geodetic(
        epoch_utc="2014-03-08T00:19:29Z",
        latitude_deg=0.0,
        longitude_deg=64.5,
        altitude_m=35_786_000.0,
    )


def _uncertainty() -> SlantRangeUncertainty:
    return SlantRangeUncertainty(
        nominal_range_m=36_000_000.0,
        timing_range_uncertainty_m=10_000.0,
        satellite_position_bias_m=250.0,
    )


def _bands() -> SlantRangeUncertaintyBands:
    return generate_uncertainty_bands(
        _satellite(),
        _uncertainty(),
        tolerance_m=10.0,
        longitude_step_deg=5.0,
        latitude_step_deg=5.0,
        minimum_longitude_deg=40.0,
        maximum_longitude_deg=90.0,
        minimum_latitude_deg=-30.0,
        maximum_latitude_deg=30.0,
    )


def test_timing_uncertainty_defines_lower_and_upper_ranges() -> None:
    uncertainty = _uncertainty()

    assert uncertainty.lower_range_m == 35_990_000.0
    assert uncertainty.upper_range_m == 36_010_000.0


def test_ordered_ranges_are_canonical() -> None:
    uncertainty = _uncertainty()

    assert uncertainty.ordered_ranges() == (
        ("lower", 35_990_000.0),
        ("nominal", 36_000_000.0),
        ("upper", 36_010_000.0),
    )


def test_satellite_position_bias_is_metadata_only() -> None:
    without_bias = SlantRangeUncertainty(
        nominal_range_m=36_000_000.0,
        timing_range_uncertainty_m=10_000.0,
        satellite_position_bias_m=0.0,
    )
    with_bias = SlantRangeUncertainty(
        nominal_range_m=36_000_000.0,
        timing_range_uncertainty_m=10_000.0,
        satellite_position_bias_m=999.0,
    )

    assert without_bias.ordered_ranges() == with_bias.ordered_ranges()
    assert with_bias.satellite_position_bias_m == 999.0


@pytest.mark.parametrize(
    "value",
    [-1.0, math.inf, -math.inf, math.nan],
)
def test_invalid_timing_uncertainty_is_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        SlantRangeUncertainty(
            nominal_range_m=36_000_000.0,
            timing_range_uncertainty_m=value,
        )


def test_non_positive_lower_range_fails_closed() -> None:
    with pytest.raises(ValueError, match="lower_range_m"):
        SlantRangeUncertainty(
            nominal_range_m=1_000.0,
            timing_range_uncertainty_m=1_000.0,
        )


def test_generated_bands_share_satellite_and_match_declared_ranges() -> None:
    result = _bands()

    assert tuple(band.identity for band in result.bands) == (
        "lower",
        "nominal",
        "upper",
    )
    assert all(band.locus.satellite == _satellite() for band in result.bands)
    assert all(
        band.locus.target_range_m == band.target_range_m
        for band in result.bands
    )
    assert tuple(band.target_range_m for band in result.bands) == (
        35_990_000.0,
        36_000_000.0,
        36_010_000.0,
    )


def test_uncertainty_band_objects_are_immutable() -> None:
    uncertainty = _uncertainty()
    result = _bands()
    band = result.bands[0]

    with pytest.raises(FrozenInstanceError):
        uncertainty.nominal_range_m = 1.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        band.target_range_m = 1.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.bands = ()  # type: ignore[misc]


def test_identical_inputs_produce_identical_results() -> None:
    assert _bands() == _bands()


def test_band_rejects_mismatched_locus_target() -> None:
    result = _bands()

    with pytest.raises(ValueError, match="locus target range"):
        SlantRangeBand(
            identity="lower",
            target_range_m=result.bands[0].target_range_m + 1.0,
            locus=result.bands[0].locus,
        )
