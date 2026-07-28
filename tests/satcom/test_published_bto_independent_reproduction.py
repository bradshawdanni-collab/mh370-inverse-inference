"""Independent reproduction checks for the #172 BTO-to-WGS84 transform."""

from __future__ import annotations

import hashlib
import math
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from pyproj import Transformer

from mh370_inverse_inference.satcom import (
    ECEFPoint,
    SatellitePosition,
    generate_surface_locus,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"

REVIEW_SHA256 = "7d5945d3c1d1cbb0328d6316ee0ac3508c3077af0c7457fd4c1b294ba03aa83e"
FROZEN_TARGET_RANGE_M = 37_861_969.39520467

SATELLITE = SatellitePosition(
    epoch_utc="2014-03-08T00:19:29.416Z",
    ecef=ECEFPoint(
        x_m=18_178_354.27195026,
        y_m=38_050_848.06484729,
        z_m=393_043.6546171822,
    ),
)
SATELLITE_TUPLE = (
    SATELLITE.ecef.x_m,
    SATELLITE.ecef.y_m,
    SATELLITE.ecef.z_m,
)

INDEPENDENT_TRANSFORMER = Transformer.from_crs(
    "EPSG:4979",
    "EPSG:4978",
    always_xy=True,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _independent_target_range_decimal() -> Decimal:
    with localcontext() as context:
        context.prec = 60
        speed_of_light = Decimal("299792458.0")
        corrected_bto = Decimal("18400.0")
        processing_bias = Decimal("-495679.0")
        timing_s = (corrected_bto - processing_bias) * Decimal("1e-6")
        half_path_m = speed_of_light * timing_s / Decimal(2)

        satellite = (
            Decimal("18178354.27195026"),
            Decimal("38050848.06484729"),
            Decimal("393043.6546171822"),
        )
        perth_ges = (
            Decimal("-2368800.0"),
            Decimal("4881100.0"),
            Decimal("-3342000.0"),
        )
        squared_range = sum(
            (satellite[index] - perth_ges[index]) ** 2 for index in range(3)
        )
        satellite_to_ges_m = squared_range.sqrt()
        return half_path_m - satellite_to_ges_m


def _independent_ecef(latitude_deg: float, longitude_deg: float) -> tuple[float, ...]:
    x_m, y_m, z_m = INDEPENDENT_TRANSFORMER.transform(
        longitude_deg,
        latitude_deg,
        0.0,
    )
    return float(x_m), float(y_m), float(z_m)


def _independent_residual_m(
    latitude_deg: float,
    longitude_deg: float,
    target_range_m: float,
) -> float:
    return (
        math.dist(
            _independent_ecef(latitude_deg, longitude_deg),
            SATELLITE_TUPLE,
        )
        - target_range_m
    )


def _independent_roots_at_longitude(
    longitude_deg: float,
    target_range_m: float,
) -> tuple[float, ...]:
    latitudes = tuple(-90.0 + index * 5.0 for index in range(37))
    roots: list[float] = []
    previous_latitude = latitudes[0]
    previous_residual = _independent_residual_m(
        previous_latitude,
        longitude_deg,
        target_range_m,
    )

    for latitude_deg in latitudes[1:]:
        residual = _independent_residual_m(
            latitude_deg,
            longitude_deg,
            target_range_m,
        )
        if previous_residual * residual < 0.0:
            lower = previous_latitude
            upper = latitude_deg
            lower_residual = previous_residual
            for _ in range(100):
                midpoint = (lower + upper) / 2.0
                midpoint_residual = _independent_residual_m(
                    midpoint,
                    longitude_deg,
                    target_range_m,
                )
                if abs(midpoint_residual) <= 1e-7:
                    break
                if lower_residual * midpoint_residual <= 0.0:
                    upper = midpoint
                else:
                    lower = midpoint
                    lower_residual = midpoint_residual
            roots.append(midpoint)

        previous_latitude = latitude_deg
        previous_residual = residual

    return tuple(roots)


def _independent_points(
    target_range_m: float,
) -> tuple[tuple[float, float, tuple[float, ...]], ...]:
    points: list[tuple[float, float, tuple[float, ...]]] = []
    for longitude_deg in range(-180, 181, 10):
        for latitude_deg in _independent_roots_at_longitude(
            float(longitude_deg),
            target_range_m,
        ):
            points.append(
                (
                    float(longitude_deg),
                    latitude_deg,
                    _independent_ecef(latitude_deg, float(longitude_deg)),
                )
            )
    return tuple(points)


def test_independent_reproduction_record_matches_frozen_sha256() -> None:
    path = PUBLISHED_DIR / "seventh_arc_bto_wgs84_independent_reproduction_v1.yaml"
    assert _sha256(path) == REVIEW_SHA256


def test_independent_decimal_range_reproduces_frozen_binary64_value() -> None:
    independent_range = _independent_target_range_decimal()
    frozen_range = Decimal(str(FROZEN_TARGET_RANGE_M))
    assert abs(independent_range - frozen_range) < Decimal("1.7e-8")


def test_independent_surface_roots_match_production_regression_locus() -> None:
    independent_range = float(_independent_target_range_decimal())
    independent_points = _independent_points(independent_range)

    production = generate_surface_locus(
        SATELLITE,
        FROZEN_TARGET_RANGE_M,
        tolerance_m=1.0,
        longitude_step_deg=10.0,
        latitude_step_deg=5.0,
    )

    assert len(independent_points) == len(production.points) == 16

    separations_m: list[float] = []
    production_residuals_m: list[float] = []
    independent_residuals_m: list[float] = []
    latitude_differences_deg: list[float] = []

    for independent, production_point in zip(
        independent_points,
        production.points,
        strict=True,
    ):
        longitude_deg, latitude_deg, independent_ecef = independent
        assert longitude_deg == production_point.geodetic.longitude_deg

        production_ecef = (
            production_point.ecef.x_m,
            production_point.ecef.y_m,
            production_point.ecef.z_m,
        )
        separations_m.append(math.dist(independent_ecef, production_ecef))
        production_residuals_m.append(
            abs(math.dist(production_ecef, SATELLITE_TUPLE) - FROZEN_TARGET_RANGE_M)
        )
        independent_residuals_m.append(
            abs(math.dist(independent_ecef, SATELLITE_TUPLE) - independent_range)
        )
        latitude_differences_deg.append(
            abs(latitude_deg - production_point.geodetic.latitude_deg)
        )

    assert max(production_residuals_m) <= 1.0
    assert max(independent_residuals_m) <= 1e-6
    assert max(separations_m) == pytest.approx(1.5278604724812659, abs=1e-6)
    assert sum(separations_m) / len(separations_m) == pytest.approx(
        0.7420162353676968,
        abs=1e-6,
    )
    assert max(latitude_differences_deg) == pytest.approx(
        0.000013784779184788931,
        abs=1e-12,
    )


def test_provenance_chain_advances_only_to_fixture_sampling_and_freeze() -> None:
    chain = (PUBLISHED_DIR / "satellite_state_provenance_chain.yaml").read_text(
        encoding="utf-8"
    )

    assert REVIEW_SHA256 in chain
    assert "PASS_FOR_PROGRESS_TO_CANONICAL_FIXTURE_SAMPLING_AND_FREEZE" in chain
    assert "benchmark_fixture.csv" in chain
    assert "status: NOT_CREATED" in chain
    assert not (PUBLISHED_DIR / "benchmark_fixture.csv").exists()
