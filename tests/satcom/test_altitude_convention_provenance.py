"""Provenance checks for the frozen #172 altitude convention record."""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"

ALTITUDE_CONVENTION_SHA256 = (
    "04006848dd912fc1d106cb095f2b8bd065689d947639c44e2dfcd37b80209319"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_altitude_convention_matches_recorded_sha256() -> None:
    path = PUBLISHED_DIR / "altitude_convention_wgs84_zero_height_v1.yaml"
    assert _sha256(path) == ALTITUDE_CONVENTION_SHA256


def test_altitude_convention_keeps_source_and_fixture_surfaces_distinct() -> None:
    path = PUBLISHED_DIR / "altitude_convention_wgs84_zero_height_v1.yaml"
    record = path.read_text(encoding="utf-8")

    assert "aircraft_altitude_m: 10000.0" in record
    assert "vertical_reference: WGS84_ELLIPSOID" in record
    assert "ellipsoidal_height_m: 0.0" in record
    assert "fixture_altitude_m_required: 0.0" in record
    assert "RECOMPUTE_BTO_LOCUS_ON_WGS84_ZERO_ELLIPSOIDAL_HEIGHT" in record
    assert (
        "Do not relabel a 10000 metre published-ring coordinate as altitude 0."
        in record
    )
    assert "output_classification: DERIVED_FROM_PUBLISHED_EVIDENCE" in record
    assert "direct_publication_coordinate_claim: false" in record


def test_provenance_chain_advances_only_to_wgs84_transformation_gate() -> None:
    chain_path = PUBLISHED_DIR / "satellite_state_provenance_chain.yaml"
    chain = chain_path.read_text(encoding="utf-8")

    assert ALTITUDE_CONVENTION_SHA256 in chain
    assert "PASS_FOR_PROGRESS_TO_DETERMINISTIC_WGS84_TRANSFORMATION" in chain
    assert "benchmark_fixture.csv" in chain
    assert "status: NOT_CREATED" in chain
    assert not (PUBLISHED_DIR / "benchmark_fixture.csv").exists()
