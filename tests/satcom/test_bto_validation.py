"""Tests for deterministic published BTO validation contracts."""

import hashlib
import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.locus import SurfaceLocusPoint
from mh370_inverse_inference.satcom.validation import (
    BTO_POINT_MATCHING_CONFIGURATION_ID,
    BTOValidationResult,
    BTOValidationSample,
    PublishedBTOBenchmark,
    PublishedBTOBenchmarkPoint,
    compare_published_bto_benchmark,
    load_published_bto_benchmark_csv,
)
from mh370_inverse_inference.satcom.wgs84 import (
    GeodeticPoint,
    geodetic_to_ecef,
)

_FIXTURE_SHA256 = "a" * 64
_CSV_HEADER = "point_id,sequence_index,longitude_deg,latitude_deg,altitude_m\n"


def _point(
    point_id: str,
    sequence_index: int,
    *,
    latitude_deg: float = -20.0,
    longitude_deg: float = 80.0,
) -> PublishedBTOBenchmarkPoint:
    return PublishedBTOBenchmarkPoint(
        point_id=point_id,
        sequence_index=sequence_index,
        geodetic=GeodeticPoint(latitude_deg, longitude_deg, 0.0),
    )


def _sample(
    point_id: str,
    sequence_index: int,
    deviation_m: float,
) -> BTOValidationSample:
    return BTOValidationSample(
        point_id=point_id,
        sequence_index=sequence_index,
        benchmark_point=GeodeticPoint(-20.0 + sequence_index, 80.0, 0.0),
        generated_point=GeodeticPoint(-20.0 + sequence_index, 80.1, 0.0),
        deviation_m=deviation_m,
    )


def _benchmark() -> PublishedBTOBenchmark:
    return PublishedBTOBenchmark(
        benchmark_id="published-bto-example-v1",
        fixture_sha256=_FIXTURE_SHA256,
        points=(
            _point("point-000", 0),
            _point("point-001", 1, latitude_deg=-19.0),
        ),
    )


def _result() -> BTOValidationResult:
    samples = (
        _sample("point-000", 0, 10.0),
        _sample("point-001", 1, 20.0),
    )
    return BTOValidationResult(
        benchmark_id="published-bto-example-v1",
        fixture_sha256=_FIXTURE_SHA256,
        model_version="l0.4",
        configuration_id="canonical-nearest-point-v1",
        samples=samples,
        maximum_deviation_m=20.0,
        mean_deviation_m=15.0,
        sample_count=2,
    )


def _csv_fixture(*rows: str, header: str = _CSV_HEADER) -> bytes:
    return (header + "".join(f"{row}\n" for row in rows)).encode("utf-8")


def _load_fixture(fixture_bytes: bytes) -> PublishedBTOBenchmark:
    return load_published_bto_benchmark_csv(
        fixture_bytes,
        benchmark_id="published-bto-example-v1",
        expected_sha256=hashlib.sha256(fixture_bytes).hexdigest(),
    )


def _surface_point(
    latitude_deg: float,
    longitude_deg: float,
) -> SurfaceLocusPoint:
    geodetic = GeodeticPoint(latitude_deg, longitude_deg, 0.0)
    return SurfaceLocusPoint(
        geodetic=geodetic,
        ecef=geodetic_to_ecef(geodetic),
    )


def test_benchmark_preserves_canonical_order_and_metadata() -> None:
    benchmark = _benchmark()

    assert benchmark.benchmark_id == "published-bto-example-v1"
    assert benchmark.fixture_sha256 == _FIXTURE_SHA256
    assert tuple(point.sequence_index for point in benchmark.points) == (0, 1)
    assert tuple(point.point_id for point in benchmark.points) == (
        "point-000",
        "point-001",
    )


def test_benchmark_rejects_duplicate_point_ids() -> None:
    with pytest.raises(ValueError, match="point_id values must be unique"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=_FIXTURE_SHA256,
            points=(_point("duplicate", 0), _point("duplicate", 1)),
        )


def test_benchmark_rejects_non_contiguous_ordering() -> None:
    with pytest.raises(ValueError, match="contiguous canonical ordering"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=_FIXTURE_SHA256,
            points=(_point("point-000", 0), _point("point-002", 2)),
        )


@pytest.mark.parametrize(
    "fixture_sha256",
    ["", "A" * 64, "g" * 64, "a" * 63, "a" * 65],
)
def test_benchmark_rejects_invalid_fixture_sha256(fixture_sha256: str) -> None:
    with pytest.raises(ValueError, match="lowercase hexadecimal SHA-256"):
        PublishedBTOBenchmark(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=fixture_sha256,
            points=(_point("point-000", 0),),
        )


def test_benchmark_points_require_zero_altitude() -> None:
    with pytest.raises(ValueError, match="zero altitude"):
        PublishedBTOBenchmarkPoint(
            point_id="point-000",
            sequence_index=0,
            geodetic=GeodeticPoint(-20.0, 80.0, 1.0),
        )


@pytest.mark.parametrize("deviation_m", [-1.0, math.inf, -math.inf, math.nan])
def test_samples_reject_invalid_deviation(deviation_m: float) -> None:
    with pytest.raises(ValueError):
        _sample("point-000", 0, deviation_m)


def test_result_reports_exact_deterministic_metrics() -> None:
    result = _result()

    assert result.maximum_deviation_m == 20.0
    assert result.mean_deviation_m == 15.0
    assert result.sample_count == 2
    assert result.benchmark_id == "published-bto-example-v1"
    assert result.model_version == "l0.4"
    assert result.configuration_id == "canonical-nearest-point-v1"


def test_result_rejects_inconsistent_sample_count() -> None:
    samples = (_sample("point-000", 0, 10.0),)

    with pytest.raises(ValueError, match="sample_count"):
        BTOValidationResult(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=_FIXTURE_SHA256,
            model_version="l0.4",
            configuration_id="canonical-nearest-point-v1",
            samples=samples,
            maximum_deviation_m=10.0,
            mean_deviation_m=10.0,
            sample_count=2,
        )


def test_result_rejects_metrics_that_do_not_match_samples() -> None:
    samples = (
        _sample("point-000", 0, 10.0),
        _sample("point-001", 1, 20.0),
    )

    with pytest.raises(ValueError, match="maximum_deviation_m"):
        BTOValidationResult(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=_FIXTURE_SHA256,
            model_version="l0.4",
            configuration_id="canonical-nearest-point-v1",
            samples=samples,
            maximum_deviation_m=19.0,
            mean_deviation_m=15.0,
            sample_count=2,
        )

    with pytest.raises(ValueError, match="mean_deviation_m"):
        BTOValidationResult(
            benchmark_id="published-bto-example-v1",
            fixture_sha256=_FIXTURE_SHA256,
            model_version="l0.4",
            configuration_id="canonical-nearest-point-v1",
            samples=samples,
            maximum_deviation_m=20.0,
            mean_deviation_m=14.0,
            sample_count=2,
        )


def test_validation_contracts_are_immutable() -> None:
    benchmark = _benchmark()
    result = _result()

    with pytest.raises(FrozenInstanceError):
        benchmark.benchmark_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.sample_count = 0  # type: ignore[misc]


def test_csv_loader_returns_checksum_verified_canonical_benchmark() -> None:
    fixture_bytes = _csv_fixture(
        "point-000,0,80.0,-20.0,0.0",
        "point-001,1,81.0,-19.0,0.0",
    )

    benchmark = _load_fixture(fixture_bytes)

    assert benchmark.fixture_sha256 == hashlib.sha256(fixture_bytes).hexdigest()
    assert tuple(point.point_id for point in benchmark.points) == (
        "point-000",
        "point-001",
    )
    assert tuple(point.sequence_index for point in benchmark.points) == (0, 1)
    assert benchmark.points[0].geodetic == GeodeticPoint(-20.0, 80.0, 0.0)


def test_csv_loader_rejects_changed_fixture_checksum() -> None:
    fixture_bytes = _csv_fixture("point-000,0,80.0,-20.0,0.0")

    with pytest.raises(ValueError, match="SHA-256"):
        load_published_bto_benchmark_csv(
            fixture_bytes,
            benchmark_id="published-bto-example-v1",
            expected_sha256="0" * 64,
        )


@pytest.mark.parametrize(
    "header",
    [
        "point_id,sequence_index,longitude_deg,latitude_deg\n",
        ("point_id,sequence_index,longitude_deg,latitude_deg,altitude_m," "extra\n"),
        "sequence_index,point_id,longitude_deg,latitude_deg,altitude_m\n",
    ],
)
def test_csv_loader_rejects_non_canonical_columns(header: str) -> None:
    fixture_bytes = _csv_fixture(
        "point-000,0,80.0,-20.0,0.0",
        header=header,
    )

    with pytest.raises(ValueError, match="columns"):
        _load_fixture(fixture_bytes)


def test_csv_loader_rejects_duplicate_ids_and_unordered_sequence() -> None:
    duplicate_fixture = _csv_fixture(
        "point-000,0,80.0,-20.0,0.0",
        "point-000,1,81.0,-19.0,0.0",
    )
    unordered_fixture = _csv_fixture(
        "point-000,1,80.0,-20.0,0.0",
        "point-001,0,81.0,-19.0,0.0",
    )

    with pytest.raises(ValueError, match="point_id values must be unique"):
        _load_fixture(duplicate_fixture)
    with pytest.raises(ValueError, match="contiguous canonical ordering"):
        _load_fixture(unordered_fixture)


@pytest.mark.parametrize(
    "row",
    [
        "point-000,0,nan,-20.0,0.0",
        "point-000,0,inf,-20.0,0.0",
        "point-000,0,80.0,-inf,0.0",
        "point-000,0,not-a-number,-20.0,0.0",
        "point-000,0,180.0,-20.0,0.0",
        "point-000,0,80.0,91.0,0.0",
        "point-000,0,80.0,-20.0,1.0",
    ],
)
def test_csv_loader_rejects_malformed_coordinates(row: str) -> None:
    with pytest.raises(ValueError):
        _load_fixture(_csv_fixture(row))


def test_csv_loader_rejects_blank_rows_and_missing_values() -> None:
    blank_row_fixture = (_CSV_HEADER + "point-000,0,80.0,-20.0,0.0\n\n").encode("utf-8")
    missing_value_fixture = _csv_fixture("point-000,0,80.0,,0.0")

    with pytest.raises(ValueError, match="blank rows"):
        _load_fixture(blank_row_fixture)
    with pytest.raises(ValueError, match="missing value"):
        _load_fixture(missing_value_fixture)


def test_benchmark_comparison_uses_sequence_index_alignment() -> None:
    benchmark = _benchmark()
    generated_points = (
        _surface_point(-20.0, 80.0),
        _surface_point(-19.0, 80.1),
    )

    result = compare_published_bto_benchmark(
        benchmark,
        generated_points,
        model_version="l0.4-test",
    )

    expected_second_deviation = geodesic_distance_m(
        benchmark.points[1].geodetic,
        generated_points[1].geodetic,
    )
    assert tuple(sample.point_id for sample in result.samples) == (
        "point-000",
        "point-001",
    )
    assert tuple(sample.sequence_index for sample in result.samples) == (0, 1)
    assert result.samples[0].generated_point == generated_points[0].geodetic
    assert result.samples[1].generated_point == generated_points[1].geodetic
    assert result.maximum_deviation_m == expected_second_deviation
    assert result.mean_deviation_m == expected_second_deviation / 2.0
    assert result.sample_count == 2
    assert result.benchmark_id == benchmark.benchmark_id
    assert result.fixture_sha256 == benchmark.fixture_sha256
    assert result.model_version == "l0.4-test"
    assert result.configuration_id == BTO_POINT_MATCHING_CONFIGURATION_ID


def test_benchmark_comparison_is_deterministic() -> None:
    benchmark = _benchmark()
    generated_points = (
        _surface_point(-20.0, 80.0),
        _surface_point(-19.0, 80.1),
    )

    first = compare_published_bto_benchmark(
        benchmark,
        generated_points,
        model_version="l0.4-test",
    )
    second = compare_published_bto_benchmark(
        benchmark,
        generated_points,
        model_version="l0.4-test",
    )

    assert first == second


def test_benchmark_comparison_rejects_count_mismatch() -> None:
    with pytest.raises(ValueError, match="count must match"):
        compare_published_bto_benchmark(
            _benchmark(),
            (_surface_point(-20.0, 80.0),),
            model_version="l0.4-test",
        )


def test_benchmark_comparison_rejects_non_locus_points() -> None:
    with pytest.raises(TypeError, match="SurfaceLocusPoint"):
        compare_published_bto_benchmark(
            _benchmark(),
            (GeodeticPoint(-20.0, 80.0, 0.0),),  # type: ignore[arg-type]
            model_version="l0.4-test",
        )


def test_benchmark_comparison_rejects_non_canonical_generated_order() -> None:
    generated_points = (
        _surface_point(-19.0, 81.0),
        _surface_point(-20.0, 80.0),
    )

    with pytest.raises(ValueError, match="canonical longitude-latitude ordering"):
        compare_published_bto_benchmark(
            _benchmark(),
            generated_points,
            model_version="l0.4-test",
        )


def test_benchmark_comparison_rejects_metadata_mismatch() -> None:
    generated_points = (
        _surface_point(-20.0, 80.0),
        _surface_point(-19.0, 80.1),
    )

    with pytest.raises(ValueError, match="model_version"):
        compare_published_bto_benchmark(
            _benchmark(),
            generated_points,
            model_version=" ",
        )
    with pytest.raises(ValueError, match="configuration_id"):
        compare_published_bto_benchmark(
            _benchmark(),
            generated_points,
            model_version="l0.4-test",
            configuration_id="nearest-point-v1",
        )
