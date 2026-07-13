"""Tests for deterministic published BTO validation contracts."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.satcom.validation import (
    BTOValidationResult,
    BTOValidationSample,
    PublishedBTOBenchmark,
    PublishedBTOBenchmarkPoint,
)
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint

_FIXTURE_SHA256 = "a" * 64


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
