"""Provenance checks for the frozen #172 Perth GES geometry record."""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"

PERTH_GES_SHA256 = "59db12275ff74a4469ff3676c0c07319df66d33234e657c52fe8de1f2384f88a"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_perth_ges_geometry_matches_recorded_sha256() -> None:
    path = PUBLISHED_DIR / "perth_ges_table2_ecef_geometry_v1.yaml"
    assert _sha256(path) == PERTH_GES_SHA256


def test_perth_ges_geometry_preserves_published_reference_boundary() -> None:
    path = PUBLISHED_DIR / "perth_ges_table2_ecef_geometry_v1.yaml"
    record = path.read_text(encoding="utf-8")

    assert "x: -2368.8" in record
    assert "y: 4881.1" in record
    assert "z: -3342.0" in record
    assert "source_specifies_separate_antenna_phase_centre_correction: false" in record
    assert (
        "repository_model_reproduction_decision: "
        "USE_PUBLISHED_TABLE2_ECEF_VECTOR_WITHOUT_ADDITIONAL_GEOMETRIC_CORRECTION"
        in record
    )
    assert "does not assert that the Table 2 ECEF vector is a surveyed RF" in record


def test_provenance_chain_advances_only_to_altitude_gate() -> None:
    chain_path = PUBLISHED_DIR / "satellite_state_provenance_chain.yaml"
    chain = chain_path.read_text(encoding="utf-8")

    assert PERTH_GES_SHA256 in chain
    assert "PASS_FOR_PROGRESS_TO_ALTITUDE_CONVENTION" in chain
    assert "benchmark_fixture.csv" in chain
    assert "status: NOT_CREATED" in chain
    assert not (PUBLISHED_DIR / "benchmark_fixture.csv").exists()
