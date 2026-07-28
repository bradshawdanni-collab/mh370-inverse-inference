"""Checks for the frozen #172 canonical seventh-arc benchmark fixture."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter
from pathlib import Path

from pyproj import Transformer

from mh370_inverse_inference.satcom import ECEFPoint, SatellitePosition, slant_range_m
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint, geodetic_to_ecef

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"
FIXTURE_PATH = PUBLISHED_DIR / "benchmark_fixture.csv"
SAMPLING_PATH = PUBLISHED_DIR / "seventh_arc_canonical_fixture_sampling_v1.yaml"
REVIEW_PATH = (
    PUBLISHED_DIR / "seventh_arc_canonical_fixture_independent_review_v1.yaml"
)

FIXTURE_SHA256 = "3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7"
SAMPLING_SHA256 = "1974f6c5e4be64b211248a34fecbf9d51aa74a9e68e03081a20e5aae4b1a8732"
REVIEW_SHA256 = "efc2f18255b934c0d1986e106b722c1fff5dc1f85fe82cacacb00a8b6639a66c"
TARGET_RANGE_M = 37_861_969.39520467
EXPECTED_HEADER = [
    "point_id",
    "sequence_index",
    "longitude_deg",
    "latitude_deg",
    "altitude_m",
]

SATELLITE = SatellitePosition(
    epoch_utc="2014-03-08T00:19:29.416Z",
    ecef=ECEFPoint(
        x_m=18_178_354.27195026,
        y_m=38_050_848.06484729,
        z_m=393_043.6546171822,
    ),
)
INDEPENDENT_TRANSFORMER = Transformer.from_crs(
    "EPSG:4979",
    "EPSG:4978",
    always_xy=True,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows() -> list[dict[str, str]]:
    with FIXTURE_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == EXPECTED_HEADER
        return list(reader)


def test_frozen_fixture_and_review_artifacts_match_recorded_hashes() -> None:
    assert _sha256(FIXTURE_PATH) == FIXTURE_SHA256
    assert _sha256(SAMPLING_PATH) == SAMPLING_SHA256
    assert _sha256(REVIEW_PATH) == REVIEW_SHA256
    assert len(FIXTURE_PATH.read_bytes()) == 7798
    assert FIXTURE_PATH.read_bytes().endswith(b"\n")


def test_fixture_schema_sequence_ordering_and_surface_are_canonical() -> None:
    rows = _rows()
    assert len(rows) == 176

    coordinates: list[tuple[float, float]] = []
    longitude_counts: Counter[float] = Counter()
    for index, row in enumerate(rows):
        longitude_deg = float(row["longitude_deg"])
        latitude_deg = float(row["latitude_deg"])
        altitude_m = float(row["altitude_m"])

        assert row["point_id"] == f"arc7-{index:04d}"
        assert int(row["sequence_index"]) == index
        assert altitude_m == 0.0
        assert math.isfinite(longitude_deg)
        assert math.isfinite(latitude_deg)
        coordinates.append((longitude_deg, latitude_deg))
        longitude_counts[longitude_deg] += 1

    assert coordinates == sorted(coordinates)
    assert len(set(coordinates)) == 176
    assert sorted(longitude_counts) == [float(value) for value in range(21, 109)]
    assert set(longitude_counts.values()) == {2}


def test_fixture_points_satisfy_frozen_range_with_production_wgs84_math() -> None:
    for row in _rows():
        point = GeodeticPoint(
            latitude_deg=float(row["latitude_deg"]),
            longitude_deg=float(row["longitude_deg"]),
            altitude_m=0.0,
        )
        residual_m = abs(
            slant_range_m(geodetic_to_ecef(point), SATELLITE) - TARGET_RANGE_M
        )
        assert residual_m <= 0.011


def test_fixture_points_satisfy_range_with_independent_pyproj_transform() -> None:
    satellite_tuple = (
        SATELLITE.ecef.x_m,
        SATELLITE.ecef.y_m,
        SATELLITE.ecef.z_m,
    )
    for row in _rows():
        longitude_deg = float(row["longitude_deg"])
        latitude_deg = float(row["latitude_deg"])
        x_m, y_m, z_m = INDEPENDENT_TRANSFORMER.transform(
            longitude_deg,
            latitude_deg,
            0.0,
        )
        residual_m = abs(
            math.dist((float(x_m), float(y_m), float(z_m)), satellite_tuple)
            - TARGET_RANGE_M
        )
        assert residual_m <= 0.011


def test_register_and_provenance_stop_at_final_admission_review() -> None:
    register = (PUBLISHED_DIR / "source_register.yaml").read_text(encoding="utf-8")
    chain = (PUBLISHED_DIR / "satellite_state_provenance_chain.yaml").read_text(
        encoding="utf-8"
    )

    assert "register_status: PROPOSED_PENDING_FINAL_ADMISSION_REVIEW" in register
    assert (
        "admission_status: FROZEN_PROPOSED_PENDING_FINAL_ADMISSION_REVIEW" in register
    )
    assert FIXTURE_SHA256 in register
    assert SAMPLING_SHA256 in register
    assert REVIEW_SHA256 in register
    assert "chain_status: PROPOSED_PENDING_FINAL_ADMISSION_REVIEW" in chain
    assert "PASS_FOR_PROGRESS_TO_FINAL_ADMISSION_REVIEW" in chain
    assert FIXTURE_SHA256 in chain
    assert "final Issue #172 admission review" in chain
