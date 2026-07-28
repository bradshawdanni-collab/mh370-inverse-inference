"""Deterministic contracts and metrics for published BTO arc validation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from statistics import fmean

from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.locus import SurfaceLocusPoint
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint

_BENCHMARK_CSV_COLUMNS = (
    "point_id",
    "sequence_index",
    "longitude_deg",
    "latitude_deg",
    "altitude_m",
)

ADMITTED_SEVENTH_ARC_BENCHMARK_ID = "mh370-seventh-arc-published-bto-v1"
ADMITTED_SEVENTH_ARC_FIXTURE_SHA256 = (
    "3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7"
)
BTO_POINT_MATCHING_CONFIGURATION_ID = "sequence-index-aligned-geodesic-v1"


@dataclass(frozen=True, slots=True)
class PublishedBTOBenchmarkPoint:
    """One ordered zero-altitude point in a fixed benchmark fixture."""

    point_id: str
    sequence_index: int
    geodetic: GeodeticPoint

    def __post_init__(self) -> None:
        _require_non_empty_string(self.point_id, "point_id")
        if type(self.sequence_index) is not int:
            raise TypeError("sequence_index must be int")
        if self.sequence_index < 0:
            raise ValueError("sequence_index must be non-negative")
        if type(self.geodetic) is not GeodeticPoint:
            raise TypeError("geodetic must be GeodeticPoint")
        if self.geodetic.altitude_m != 0.0:
            raise ValueError("benchmark points must have zero altitude")


@dataclass(frozen=True, slots=True)
class PublishedBTOBenchmark:
    """Immutable ordered repository-local published BTO benchmark."""

    benchmark_id: str
    fixture_sha256: str
    points: tuple[PublishedBTOBenchmarkPoint, ...]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.benchmark_id, "benchmark_id")
        _require_sha256(self.fixture_sha256)
        if type(self.points) is not tuple:
            raise TypeError("points must be tuple")
        if not self.points:
            raise ValueError("points must not be empty")
        if any(type(point) is not PublishedBTOBenchmarkPoint for point in self.points):
            raise TypeError("points must contain PublishedBTOBenchmarkPoint values")

        point_ids = tuple(point.point_id for point in self.points)
        if len(set(point_ids)) != len(point_ids):
            raise ValueError("benchmark point_id values must be unique")

        sequence = tuple(point.sequence_index for point in self.points)
        if sequence != tuple(range(len(self.points))):
            raise ValueError("benchmark points must use contiguous canonical ordering")

        coordinates = tuple(
            (point.geodetic.longitude_deg, point.geodetic.latitude_deg)
            for point in self.points
        )
        if len(set(coordinates)) != len(coordinates):
            raise ValueError("benchmark coordinates must be unique")
        if coordinates != tuple(sorted(coordinates)):
            raise ValueError("benchmark points must use longitude-latitude ordering")


@dataclass(frozen=True, slots=True)
class BTOValidationSample:
    """One deterministic benchmark-to-generated-point deviation record."""

    point_id: str
    sequence_index: int
    benchmark_point: GeodeticPoint
    generated_point: GeodeticPoint
    deviation_m: float

    def __post_init__(self) -> None:
        _require_non_empty_string(self.point_id, "point_id")
        if type(self.sequence_index) is not int:
            raise TypeError("sequence_index must be int")
        if self.sequence_index < 0:
            raise ValueError("sequence_index must be non-negative")
        if type(self.benchmark_point) is not GeodeticPoint:
            raise TypeError("benchmark_point must be GeodeticPoint")
        if type(self.generated_point) is not GeodeticPoint:
            raise TypeError("generated_point must be GeodeticPoint")
        if self.benchmark_point.altitude_m != 0.0:
            raise ValueError("benchmark_point must have zero altitude")
        if self.generated_point.altitude_m != 0.0:
            raise ValueError("generated_point must have zero altitude")
        _require_non_negative_finite(self.deviation_m, "deviation_m")


@dataclass(frozen=True, slots=True)
class BTOValidationResult:
    """Canonical deterministic summary of one benchmark validation."""

    benchmark_id: str
    fixture_sha256: str
    model_version: str
    configuration_id: str
    samples: tuple[BTOValidationSample, ...]
    maximum_deviation_m: float
    mean_deviation_m: float
    sample_count: int

    def __post_init__(self) -> None:
        _require_non_empty_string(self.benchmark_id, "benchmark_id")
        _require_sha256(self.fixture_sha256)
        _require_non_empty_string(self.model_version, "model_version")
        _require_non_empty_string(self.configuration_id, "configuration_id")
        if type(self.samples) is not tuple:
            raise TypeError("samples must be tuple")
        if not self.samples:
            raise ValueError("samples must not be empty")
        if any(type(sample) is not BTOValidationSample for sample in self.samples):
            raise TypeError("samples must contain BTOValidationSample values")

        sequence = tuple(sample.sequence_index for sample in self.samples)
        if sequence != tuple(range(len(self.samples))):
            raise ValueError("samples must use contiguous canonical ordering")

        if type(self.sample_count) is not int:
            raise TypeError("sample_count must be int")
        if self.sample_count != len(self.samples):
            raise ValueError("sample_count must equal the number of samples")

        _require_non_negative_finite(
            self.maximum_deviation_m,
            "maximum_deviation_m",
        )
        _require_non_negative_finite(self.mean_deviation_m, "mean_deviation_m")

        deviations = tuple(sample.deviation_m for sample in self.samples)
        if self.maximum_deviation_m != max(deviations):
            raise ValueError("maximum_deviation_m must match samples")
        if self.mean_deviation_m != math.fsum(deviations) / len(deviations):
            raise ValueError("mean_deviation_m must match samples")


@dataclass(frozen=True, slots=True)
class ValidationMetrics:
    """Backward-compatible summary statistics for locus deviation."""

    benchmark_id: str
    model_version: str
    sample_count: int
    mean_deviation_m: float
    maximum_deviation_m: float


def load_published_bto_benchmark_csv(
    fixture_bytes: bytes,
    *,
    benchmark_id: str,
    expected_sha256: str,
) -> PublishedBTOBenchmark:
    """Load one checksum-verified canonical benchmark fixture from CSV bytes."""
    if type(fixture_bytes) is not bytes:
        raise TypeError("fixture_bytes must be bytes")
    _require_non_empty_string(benchmark_id, "benchmark_id")
    _require_sha256(expected_sha256)

    actual_sha256 = hashlib.sha256(fixture_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("fixture SHA-256 does not match expected_sha256")
    if not fixture_bytes.endswith(b"\n"):
        raise ValueError("fixture must end with a final LF newline")
    if b"\r" in fixture_bytes:
        raise ValueError("fixture must use LF line endings")

    try:
        text = fixture_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("fixture must be valid UTF-8") from error

    lines = text.splitlines()
    if not lines:
        raise ValueError("fixture must not be empty")
    if any(not line.strip() for line in lines):
        raise ValueError("fixture must not contain blank rows")

    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != list(_BENCHMARK_CSV_COLUMNS):
            raise ValueError(
                "fixture columns must exactly match canonical benchmark columns"
            )

        points = tuple(
            _benchmark_point_from_csv_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        )
    except csv.Error as error:
        raise ValueError("fixture must be valid CSV") from error

    return PublishedBTOBenchmark(
        benchmark_id=benchmark_id,
        fixture_sha256=actual_sha256,
        points=points,
    )


def load_admitted_seventh_arc_benchmark(
    fixture_bytes: bytes,
) -> PublishedBTOBenchmark:
    """Load only the exact Issue #172-admitted seventh-arc fixture bytes."""
    return load_published_bto_benchmark_csv(
        fixture_bytes,
        benchmark_id=ADMITTED_SEVENTH_ARC_BENCHMARK_ID,
        expected_sha256=ADMITTED_SEVENTH_ARC_FIXTURE_SHA256,
    )


def compare_published_bto_benchmark(
    benchmark: PublishedBTOBenchmark,
    generated_points: tuple[SurfaceLocusPoint, ...],
    *,
    model_version: str,
    configuration_id: str = BTO_POINT_MATCHING_CONFIGURATION_ID,
) -> BTOValidationResult:
    """Compare canonical points using exact sequence-index alignment.

    Benchmark point ``i`` is matched only with generated locus point ``i``.
    Deviations are WGS84 ellipsoidal surface distances in metres.
    """
    if type(benchmark) is not PublishedBTOBenchmark:
        raise TypeError("benchmark must be PublishedBTOBenchmark")
    if type(generated_points) is not tuple:
        raise TypeError("generated_points must be tuple")
    if any(type(point) is not SurfaceLocusPoint for point in generated_points):
        raise TypeError("generated_points must contain SurfaceLocusPoint values")
    if len(generated_points) != len(benchmark.points):
        raise ValueError("generated_points count must match benchmark points")

    _require_non_empty_string(model_version, "model_version")
    _require_non_empty_string(configuration_id, "configuration_id")
    if configuration_id != BTO_POINT_MATCHING_CONFIGURATION_ID:
        raise ValueError(
            "configuration_id must match the sequence-index alignment contract"
        )

    generated_order = tuple(
        (point.geodetic.longitude_deg, point.geodetic.latitude_deg)
        for point in generated_points
    )
    if generated_order != tuple(sorted(generated_order)):
        raise ValueError(
            "generated_points must use canonical longitude-latitude ordering"
        )

    samples = tuple(
        BTOValidationSample(
            point_id=benchmark_point.point_id,
            sequence_index=benchmark_point.sequence_index,
            benchmark_point=benchmark_point.geodetic,
            generated_point=generated_point.geodetic,
            deviation_m=geodesic_distance_m(
                benchmark_point.geodetic,
                generated_point.geodetic,
            ),
        )
        for benchmark_point, generated_point in zip(
            benchmark.points,
            generated_points,
            strict=True,
        )
    )
    deviations = tuple(sample.deviation_m for sample in samples)

    return BTOValidationResult(
        benchmark_id=benchmark.benchmark_id,
        fixture_sha256=benchmark.fixture_sha256,
        model_version=model_version,
        configuration_id=configuration_id,
        samples=samples,
        maximum_deviation_m=max(deviations),
        mean_deviation_m=math.fsum(deviations) / len(deviations),
        sample_count=len(samples),
    )


def serialize_bto_validation_result_json(result: BTOValidationResult) -> bytes:
    """Serialize a validation result as stable UTF-8 JSON with an LF newline."""
    if type(result) is not BTOValidationResult:
        raise TypeError("result must be BTOValidationResult")

    payload = {
        "benchmark_id": result.benchmark_id,
        "configuration_id": result.configuration_id,
        "fixture_sha256": result.fixture_sha256,
        "maximum_deviation_m": result.maximum_deviation_m,
        "mean_deviation_m": result.mean_deviation_m,
        "model_version": result.model_version,
        "sample_count": result.sample_count,
        "samples": [
            {
                "deviation_m": sample.deviation_m,
                "point_id": sample.point_id,
                "sequence_index": sample.sequence_index,
            }
            for sample in result.samples
        ],
        "units": {"deviation": "metres"},
    }
    text = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{text}\n".encode()


def nearest_reference_distance_m(
    point: GeodeticPoint,
    reference_points: tuple[GeodeticPoint, ...],
) -> float:
    """Return the nearest WGS84 geodesic distance to a reference point."""
    if not reference_points:
        raise ValueError("reference_points must not be empty")
    return min(geodesic_distance_m(point, reference) for reference in reference_points)


def compare_loci(
    generated_points: tuple[GeodeticPoint, ...],
    reference_points: tuple[GeodeticPoint, ...],
    *,
    benchmark_id: str,
    model_version: str,
) -> ValidationMetrics:
    """Compare generated points with a reference locus using nearest distances."""
    if not generated_points:
        raise ValueError("generated_points must not be empty")
    if not reference_points:
        raise ValueError("reference_points must not be empty")

    deviations = tuple(
        nearest_reference_distance_m(point, reference_points)
        for point in generated_points
    )
    return ValidationMetrics(
        benchmark_id=benchmark_id,
        model_version=model_version,
        sample_count=len(deviations),
        mean_deviation_m=fmean(deviations),
        maximum_deviation_m=max(deviations),
    )


def _benchmark_point_from_csv_row(
    row: dict[str | None, str | list[str] | None],
    row_number: int,
) -> PublishedBTOBenchmarkPoint:
    if set(row) != set(_BENCHMARK_CSV_COLUMNS):
        raise ValueError(f"fixture row {row_number} has missing or additional columns")

    values: dict[str, str] = {}
    for column in _BENCHMARK_CSV_COLUMNS:
        value = row[column]
        if type(value) is not str or not value:
            raise ValueError(f"fixture row {row_number} contains a missing value")
        if value != value.strip():
            raise ValueError(
                f"fixture row {row_number} contains surrounding whitespace"
            )
        values[column] = value

    sequence_text = values["sequence_index"]
    if not sequence_text.isascii() or not sequence_text.isdecimal():
        raise ValueError(f"fixture row {row_number} has invalid sequence_index")
    sequence_index = int(sequence_text)
    if sequence_text != str(sequence_index):
        raise ValueError(f"fixture row {row_number} has non-canonical sequence_index")

    longitude_deg = _parse_finite_float(
        values["longitude_deg"],
        "longitude_deg",
        row_number,
    )
    if not -180.0 <= longitude_deg < 180.0:
        raise ValueError(
            f"fixture row {row_number} longitude_deg must be within [-180, 180)"
        )
    latitude_deg = _parse_finite_float(
        values["latitude_deg"],
        "latitude_deg",
        row_number,
    )
    altitude_m = _parse_finite_float(
        values["altitude_m"],
        "altitude_m",
        row_number,
    )

    return PublishedBTOBenchmarkPoint(
        point_id=values["point_id"],
        sequence_index=sequence_index,
        geodetic=GeodeticPoint(
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            altitude_m=altitude_m,
        ),
    )


def _parse_finite_float(value: str, name: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except ValueError as error:
        raise ValueError(f"fixture row {row_number} has invalid {name}") from error
    if not math.isfinite(parsed):
        raise ValueError(f"fixture row {row_number} {name} must be finite")
    return parsed


def _require_non_empty_string(value: str, name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_sha256(value: str) -> None:
    if type(value) is not str:
        raise TypeError("fixture_sha256 must be str")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(
            "fixture_sha256 must be a lowercase hexadecimal SHA-256 digest"
        )


def _require_non_negative_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")
