"""Deterministic tests for the frozen #172 BTO-to-WGS84 transformation."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from mh370_inverse_inference.satcom import (
    ECEFPoint,
    SatellitePosition,
    generate_published_bto_zero_height_locus,
    published_bto_aircraft_range_m,
    slant_range_m,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"
TRANSFORM_SHA256 = "4142c33134df8704a466e037b0e1cb065116daea06b74307a986274509f2db21"
PENDING_FIXTURE_STATUS = "FROZEN_PROPOSED_PENDING_FINAL_ADMISSION_REVIEW"

SATELLITE = SatellitePosition(
    epoch_utc="2014-03-08T00:19:29.416Z",
    ecef=ECEFPoint(
        x_m=18_178_354.27195026,
        y_m=38_050_848.06484729,
        z_m=393_043.6546171822,
    ),
)
PERTH_GES = ECEFPoint(
    x_m=-2_368_800.0,
    y_m=4_881_100.0,
    z_m=-3_342_000.0,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_transform_contract_matches_frozen_sha256() -> None:
    path = PUBLISHED_DIR / "seventh_arc_bto_wgs84_transform_v1.yaml"
    assert _sha256(path) == TRANSFORM_SHA256


def test_published_bto_range_matches_frozen_reference_value() -> None:
    result = published_bto_aircraft_range_m(
        corrected_bto_microseconds=18_400.0,
        fixed_processing_bias_microseconds=-495_679.0,
        satellite=SATELLITE,
        perth_ges_ecef=PERTH_GES,
    )

    assert math.isclose(result, 37_861_969.39520467, rel_tol=0.0, abs_tol=1e-6)


def test_published_bto_range_rejects_invalid_timing_inputs() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        published_bto_aircraft_range_m(
            corrected_bto_microseconds=-1.0,
            fixed_processing_bias_microseconds=-495_679.0,
            satellite=SATELLITE,
            perth_ges_ecef=PERTH_GES,
        )

    with pytest.raises(ValueError, match="BTO minus processing bias"):
        published_bto_aircraft_range_m(
            corrected_bto_microseconds=18_400.0,
            fixed_processing_bias_microseconds=18_400.0,
            satellite=SATELLITE,
            perth_ges_ecef=PERTH_GES,
        )


def test_zero_height_locus_is_deterministic_and_range_consistent() -> None:
    first = generate_published_bto_zero_height_locus(
        corrected_bto_microseconds=18_400.0,
        fixed_processing_bias_microseconds=-495_679.0,
        satellite=SATELLITE,
        perth_ges_ecef=PERTH_GES,
        tolerance_m=1.0,
        longitude_step_deg=10.0,
        latitude_step_deg=5.0,
    )
    second = generate_published_bto_zero_height_locus(
        corrected_bto_microseconds=18_400.0,
        fixed_processing_bias_microseconds=-495_679.0,
        satellite=SATELLITE,
        perth_ges_ecef=PERTH_GES,
        tolerance_m=1.0,
        longitude_step_deg=10.0,
        latitude_step_deg=5.0,
    )

    assert first == second
    assert len(first.points) == 16
    assert first.target_range_m == pytest.approx(37_861_969.39520467, abs=1e-6)
    assert all(point.geodetic.altitude_m == 0.0 for point in first.points)
    assert all(
        abs(slant_range_m(point.ecef, SATELLITE) - first.target_range_m) <= 1.0
        for point in first.points
    )
    assert list(first.points) == sorted(
        first.points,
        key=lambda point: (
            point.geodetic.longitude_deg,
            point.geodetic.latitude_deg,
        ),
    )


def test_provenance_chain_preserves_transform_gate_after_fixture_freeze() -> None:
    chain = (PUBLISHED_DIR / "satellite_state_provenance_chain.yaml").read_text(
        encoding="utf-8"
    )
    fixture_path = PUBLISHED_DIR / "benchmark_fixture.csv"

    assert TRANSFORM_SHA256 in chain
    assert "IMPLEMENTED_PENDING_INDEPENDENT_REPRODUCTION" in chain
    assert "benchmark_fixture.csv" in chain
    assert f"status: {PENDING_FIXTURE_STATUS}" in chain
    assert fixture_path.exists()
    assert "status: ADMITTED" not in chain
