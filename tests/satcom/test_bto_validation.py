"""Tests for deterministic Issue #7 published BTO validation contracts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mh370_inverse_inference.satcom import (
    ADMITTED_SEVENTH_ARC_BENCHMARK_ID,
    ADMITTED_SEVENTH_ARC_FIXTURE_SHA256,
    BTO_POINT_MATCHING_CONFIGURATION_ID,
    BTOValidationResult,
    BTOValidationSample,
    ECEFPoint,
    PublishedBTOBenchmark,
    PublishedBTOBenchmarkPoint,
    SatellitePosition,
    SurfaceLocusPoint,
    compare_published_bto_benchmark,
    generate_surface_locus,
    geodetic_to_ecef,
    load_admitted_seventh_arc_benchmark,
    load_published_bto_benchmark_csv,
    serialize_bto_validation_result_json,
)
from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "data" / "satcom" / "published" / "benchmark_fixture.csv"
CSV_HEADER = "point_id,sequence_index,longitude_deg,latitude_deg,altitude_m\n"
TEST_SHA256 = "a" * 64
TARGET_RANGE_M = 37_861_969.39520467
SATELLITE = SatellitePosition(
    epoch_utc="2014-03-08T00:19:29.416Z",
    ecef=ECEFPoint(
        x_m=18_178_354.27195026,
        y_m=38_050_848.06484729,
        z_m=393_043.6546171822,
    ),
)


def _benchmark_point(
    point_id: str,
    sequence_index: int,
    *,
    longitude_deg: float,
    latitude_deg: float,
) -> PublishedBTOBenchmarkPoint:
    return PublishedBTOBenchmarkPoint(
        point_id=point_id,
        sequence_index=sequence_index,
        geodetic=GeodeticPoint(latitude_deg, longitude_deg, 0.0),
    )


def _surface_point(latitude_deg: float, longitude_deg: float) -> SurfaceLocusPoint:
    geodetic = GeodeticPoint(latitude_deg, longitude_deg, 0.0)
    return SurfaceLocusPoint(
        geodetic=geodetic,
        ecef=geodetic_to_ecef(geodetic),
    )


def _csv_fixture(*rows: str, header: str = CSV_HEADER) -> bytes:
    return (header + "".join(f"{row}\n" for row in rows)).encode("utf-8")


def _load_fixture(fixture_bytes: bytes) -> PublishedBTOBenchmark:
    return load_published_bto_benchmark_csv(
        fixture_bytes,
        benchmark_id="published-bto-example-v1",
        expected_sha256=hashlib.sha256(fixture_bytes).hexdigest(),
    )


def _benchmark() -> PublishedBTOBenchmark:
    return PublishedBTOBenchmark(
        benchmark_id="published-bto-example-v1",
        fixture_sha256=TEST_SHA256,
        points=(
            _benchmark_point(
                "point-000",
                0,
                longitude_deg=80.0,
                latitude_deg=-20.0,
            ),
            _benchmark_point(
                "point-001",
                1,
                longitude_deg=81.0,
                latitude_deg=-19.0,
            ),
        ),
    )


def test_benchmark_contract_is_immutable_and_canonically_ordered() -> None:
    benchmark = _benchmark()

    assert tuple(point.sequence_index for point in benchmark.points) == (0, 1)
    assert tuple(point.point_id for point in benchmark.points) == (
        "point-000",
        "point-001",
    )
    with pytest.raises(FrozenInstanceError):
        benchmark.benchmark_id = "changed"  # type: ignore[misc]


def test_benchmark_rejects_duplicate_ids_coordinates_and_bad_order() -> None:
    first = _benchmark_point(
        "point-000",
        0,
        longitude_deg=80.0,
        latitude_deg=-20.0,
    )

    with pytest.raises(ValueError, match="point_id values must be unique"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=TEST_SHA256,
            points=(
                first,
                _benchmark_point(
                    "point-000",
                    1,
                    longitude_deg=81.0,
                    latitude_deg=-19.0,
                ),
            ),
        )

    with pytest.raises(ValueError, match="coordinates must be unique"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=TEST_SHA256,
            points=(
                first,
                _benchmark_point(
                    "point-001",
                    1,
                    longitude_deg=80.0,
                    latitude_deg=-20.0,
                ),
            ),
        )

    with pytest.raises(ValueError, match="longitude-latitude ordering"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=TEST_SHA256,
            points=(
                _benchmark_point(
                    "point-000",
                    0,
                    longitude_deg=81.0,
                    latitude_deg=-19.0,
                ),
                _benchmark_point(
                    "point-001",
                    1,
                    longitude_deg=80.0,
                    latitude_deg=-20.0,
                ),
            ),
        )


def test_benchmark_rejects_non_contiguous_sequence_and_nonzero_altitude() -> None:
    with pytest.raises(ValueError, match="contiguous canonical ordering"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=TEST_SHA256,
            points=(
                _benchmark_point(
                    "point-000",
                    0,
                    longitude_deg=80.0,
                    latitude_deg=-20.0,
                ),
                _benchmark_point(
                    "point-002",
                    2,
                    longitude_deg=81.0,
                    latitude_deg=-19.0,
                ),
            ),
        )

    with pytest.raises(ValueError, match="zero altitude"):
        PublishedBTOBenchmarkPoint(
            point_id="point-000",
            sequence_index=0,
            geodetic=GeodeticPoint(-20.0, 80.0, 1.0),
        )


def test_csv_loader_verifies_checksum_schema_serialization_and_order() -> None:
    fixture_bytes = _csv_fixture(
        "point-000,0,80.0,-20.0,0.0",
        "point-001,1,81.0,-19.0,0.0",
    )
    benchmark = _load_fixture(fixture_bytes)

    assert benchmark.fixture_sha256 == hashlib.sha256(fixture_bytes).hexdigest()
    assert len(benchmark.points) == 2

    with pytest.raises(ValueError, match="SHA-256"):
        load_published_bto_benchmark_csv(
            fixture_bytes,
            benchmark_id="published-bto-example-v1",
            expected_sha256="0" * 64,
        )

    no_final_newline = fixture_bytes.removesuffix(b"\n")
    with pytest.raises(ValueError, match="final LF newline"):
        _load_fixture(no_final_newline)

    crlf_fixture = fixture_bytes.replace(b"\n", b"\r\n")
    with pytest.raises(ValueError, match="LF line endings"):
        _load_fixture(crlf_fixture)


def test_csv_loader_fails_closed_on_ambiguous_or_malformed_rows() -> None:
    bad_header = "sequence_index,point_id,longitude_deg,latitude_deg,altitude_m\n"
    with pytest.raises(ValueError, match="columns"):
        _load_fixture(
            _csv_fixture(
                "0,point-000,80.0,-20.0,0.0",
                header=bad_header,
            )
        )

    with pytest.raises(ValueError, match="blank rows"):
        _load_fixture(
            (CSV_HEADER + "point-000,0,80.0,-20.0,0.0\n\n").encode("utf-8")
        )

    with pytest.raises(ValueError, match="point_id values must be unique"):
        _load_fixture(
            _csv_fixture(
                "point-000,0,80.0,-20.0,0.0",
                "point-000,1,81.0,-19.0,0.0",
            )
        )

    with pytest.raises(ValueError, match="longitude-latitude ordering"):
        _load_fixture(
            _csv_fixture(
                "point-000,0,81.0,-19.0,0.0",
                "point-001,1,80.0,-20.0,0.0",
            )
        )

    for row in (
        "point-000,0,nan,-20.0,0.0",
        "point-000,0,inf,-20.0,0.0",
        "point-000,0,180.0,-20.0,0.0",
        "point-000,0,80.0,91.0,0.0",
        "point-000,0,80.0,-20.0,1.0",
    ):
        with pytest.raises(ValueError):
            _load_fixture(_csv_fixture(row))


def test_comparison_uses_exact_sequence_alignment_and_reports_metres() -> None:
    benchmark = _benchmark()
    generated_points = (
        _surface_point(-20.0, 80.0),
        _surface_point(-19.0, 81.1),
    )

    result = compare_published_bto_benchmark(
        benchmark,
        generated_points,
        model_version="l0.4-test",
    )
    expected_second = geodesic_distance_m(
        benchmark.points[1].geodetic,
        generated_points[1].geodetic,
    )

    assert result.sample_count == 2
    assert result.maximum_deviation_m == expected_second
    assert result.mean_deviation_m == expected_second / 2.0
    assert result.configuration_id == BTO_POINT_MATCHING_CONFIGURATION_ID
    assert result.samples[0].point_id == "point-000"
    assert result.samples[1].point_id == "point-001"


def test_comparison_rejects_count_order_and_configuration_mismatch() -> None:
    benchmark = _benchmark()

    with pytest.raises(ValueError, match="count must match"):
        compare_published_bto_benchmark(
            benchmark,
            (_surface_point(-20.0, 80.0),),
            model_version="l0.4-test",
        )

    with pytest.raises(ValueError, match="canonical longitude-latitude ordering"):
        compare_published_bto_benchmark(
            benchmark,
            (
                _surface_point(-19.0, 81.0),
                _surface_point(-20.0, 80.0),
            ),
            model_version="l0.4-test",
        )

    with pytest.raises(ValueError, match="configuration_id"):
        compare_published_bto_benchmark(
            benchmark,
            (
                _surface_point(-20.0, 80.0),
                _surface_point(-19.0, 81.0),
            ),
            model_version="l0.4-test",
            configuration_id="nearest-point-v1",
        )


def test_result_rejects_non_finite_or_inconsistent_metrics() -> None:
    sample = BTOValidationSample(
        point_id="point-000",
        sequence_index=0,
        benchmark_point=GeodeticPoint(-20.0, 80.0, 0.0),
        generated_point=GeodeticPoint(-20.0, 80.1, 0.0),
        deviation_m=10.0,
    )

    with pytest.raises(ValueError, match="sample_count"):
        BTOValidationResult(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=TEST_SHA256,
            model_version="l0.4-test",
            configuration_id=BTO_POINT_MATCHING_CONFIGURATION_ID,
            samples=(sample,),
            maximum_deviation_m=10.0,
            mean_deviation_m=10.0,
            sample_count=2,
        )

    for deviation in (-1.0, math.inf, -math.inf, math.nan):
        with pytest.raises(ValueError):
            BTOValidationSample(
                point_id="point-000",
                sequence_index=0,
                benchmark_point=GeodeticPoint(-20.0, 80.0, 0.0),
                generated_point=GeodeticPoint(-20.0, 80.1, 0.0),
                deviation_m=deviation,
            )


def test_validation_json_is_stable_machine_readable_output() -> None:
    result = compare_published_bto_benchmark(
        _benchmark(),
        (
            _surface_point(-20.0, 80.0),
            _surface_point(-19.0, 81.1),
        ),
        model_version="l0.4-test",
    )

    first = serialize_bto_validation_result_json(result)
    second = serialize_bto_validation_result_json(result)
    payload = json.loads(first)

    assert first == second
    assert first.endswith(b"\n")
    assert payload["benchmark_id"] == "published-bto-example-v1"
    assert payload["configuration_id"] == BTO_POINT_MATCHING_CONFIGURATION_ID
    assert payload["sample_count"] == 2
    assert payload["units"] == {"deviation": "metres"}


def test_admitted_fixture_is_consumed_exactly_without_regeneration() -> None:
    fixture_bytes = FIXTURE_PATH.read_bytes()
    benchmark = load_admitted_seventh_arc_benchmark(fixture_bytes)
    fixture_sha256 = hashlib.sha256(fixture_bytes).hexdigest()

    assert fixture_sha256 == ADMITTED_SEVENTH_ARC_FIXTURE_SHA256
    assert benchmark.benchmark_id == ADMITTED_SEVENTH_ARC_BENCHMARK_ID
    assert benchmark.fixture_sha256 == ADMITTED_SEVENTH_ARC_FIXTURE_SHA256
    assert len(benchmark.points) == 176
    assert benchmark.points[0].point_id == "arc7-0000"
    assert benchmark.points[-1].sequence_index == 175


def test_admitted_fixture_validates_against_existing_l02_surface_solver() -> None:
    benchmark = load_admitted_seventh_arc_benchmark(FIXTURE_PATH.read_bytes())
    generated = generate_surface_locus(
        SATELLITE,
        TARGET_RANGE_M,
        tolerance_m=0.01,
        longitude_step_deg=1.0,
        latitude_step_deg=0.25,
        minimum_longitude_deg=-180.0,
        maximum_longitude_deg=179.0,
        minimum_latitude_deg=-90.0,
        maximum_latitude_deg=90.0,
        maximum_iterations=80,
    )

    result = compare_published_bto_benchmark(
        benchmark,
        generated.points,
        model_version="l0.4-wgs84-v1",
    )

    assert result.benchmark_id == ADMITTED_SEVENTH_ARC_BENCHMARK_ID
    assert result.fixture_sha256 == ADMITTED_SEVENTH_ARC_FIXTURE_SHA256
    assert result.configuration_id == BTO_POINT_MATCHING_CONFIGURATION_ID
    assert result.sample_count == 176
    assert result.maximum_deviation_m <= 0.1
    assert result.mean_deviation_m <= result.maximum_deviation_m

    encoded = serialize_bto_validation_result_json(result)
    assert encoded == serialize_bto_validation_result_json(result)
