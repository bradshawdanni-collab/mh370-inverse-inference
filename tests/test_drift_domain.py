"""Tests for L8 drift-domain validation records."""

import math

import pytest

from mh370_inverse_inference.drift.domain import (
    DriftDomain,
    EnvironmentalSample,
    NumericRange,
)


def test_numeric_range_contains_inclusive_bounds() -> None:
    parameter = NumericRange(name="windage", lower=0.0, upper=0.05)

    assert parameter.contains(0.0)
    assert parameter.contains(0.025)
    assert parameter.contains(0.05)
    assert not parameter.contains(0.051)


def test_numeric_range_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="required"):
        NumericRange(name="", lower=0.0, upper=1.0)

    with pytest.raises(ValueError, match="finite"):
        NumericRange(name="x", lower=0.0, upper=math.inf)

    with pytest.raises(ValueError, match="below"):
        NumericRange(name="x", lower=2.0, upper=1.0)


def test_environmental_sample_accepts_finite_non_negative_inputs() -> None:
    sample = EnvironmentalSample(
        current_speed_mps=0.5,
        wind_speed_mps=8.0,
        wave_height_m=1.2,
        sea_surface_temperature_c=24.0,
    )

    assert sample.current_speed_mps == 0.5


def test_environmental_sample_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        EnvironmentalSample(
            current_speed_mps=math.nan,
            wind_speed_mps=8.0,
            wave_height_m=1.2,
            sea_surface_temperature_c=24.0,
        )


def test_environmental_sample_rejects_negative_magnitudes() -> None:
    with pytest.raises(ValueError, match="current speed"):
        EnvironmentalSample(
            current_speed_mps=-0.1,
            wind_speed_mps=8.0,
            wave_height_m=1.2,
            sea_surface_temperature_c=24.0,
        )

    with pytest.raises(ValueError, match="wind speed"):
        EnvironmentalSample(
            current_speed_mps=0.5,
            wind_speed_mps=-1.0,
            wave_height_m=1.2,
            sea_surface_temperature_c=24.0,
        )

    with pytest.raises(ValueError, match="wave height"):
        EnvironmentalSample(
            current_speed_mps=0.5,
            wind_speed_mps=8.0,
            wave_height_m=-0.1,
            sea_surface_temperature_c=24.0,
        )


def test_drift_domain_preserves_order_and_validates_points() -> None:
    domain = DriftDomain(
        parameters=(
            NumericRange(name="windage", lower=0.0, upper=0.05),
            NumericRange(name="diffusivity", lower=0.0, upper=5.0),
        )
    )

    domain.validate_point({"diffusivity": 2.0, "windage": 0.02})
    assert domain.names == ("windage", "diffusivity")


def test_drift_domain_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError, match="unique"):
        DriftDomain(
            parameters=(
                NumericRange(name="x", lower=0.0, upper=1.0),
                NumericRange(name="x", lower=0.0, upper=2.0),
            )
        )


def test_drift_domain_rejects_missing_or_out_of_range_values() -> None:
    domain = DriftDomain(
        parameters=(NumericRange(name="windage", lower=0.0, upper=0.05),)
    )

    with pytest.raises(ValueError, match="keys"):
        domain.validate_point({"other": 0.01})

    with pytest.raises(ValueError, match="outside"):
        domain.validate_point({"windage": 0.10})
