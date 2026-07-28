"""Independent reproduction checks for the frozen #172 satellite-state chain."""

from __future__ import annotations

import hashlib
import math
from decimal import Decimal, localcontext
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"
DOCS_SATCOM_DIR = REPO_ROOT / "docs" / "satcom"

ENDPOINTS_SHA256 = "835c5a93ca9af0c618bb692404a8af59a079aa08af3188df0abcaa3b515eebbc"
TRANSFORM_SHA256 = "ea135509fc6d1dcc9e2f5dad07780ad74e976337a02ba073351f243c1b79ee82"
TARGET_STATE_SHA256 = "c61f400c8b27b07b3acc57701d958068ee8cbb2654a5e325e3f2d0f0cb166452"
SOURCE_PDF_SHA256 = "2ff0f10c1cf0bad299e5398ad9019a113963f6a5bd86b96bf4d04d330bc08028"
PROOF_SHA256 = "6ac053c8417707c71766b5a90981e406d77a4f3e6cdbc36553b705ce6284ae4a"
REVIEW_SHA256 = "f661f502be4d267a583b7efd1f770a445cbdbe478f17acfa8339978bde1d0dce"
PENDING_FIXTURE_STATUS = "FROZEN_PROPOSED_PENDING_FINAL_ADMISSION_REVIEW"

FROZEN_HASHES = {
    "inmarsat_3f1_table4_endpoints.yaml": ENDPOINTS_SHA256,
    "inmarsat_3f1_hermite_transform_v1.yaml": TRANSFORM_SHA256,
    "inmarsat_3f1_target_state_20140308T001929416Z.yaml": TARGET_STATE_SHA256,
}

DURATION_S = 600.0
TARGET_OFFSET_S = 569.416

FROZEN_POSITION_M = (
    18_178_354.27195026,
    38_050_848.06484729,
    393_043.6546171822,
)
FROZEN_VELOCITY_M_S = (
    1.4905848175466667,
    -1.5633706024564664,
    -83.12914420245867,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hermite_binary64(
    start_position: float,
    start_velocity: float,
    end_position: float,
    end_velocity: float,
) -> tuple[float, float]:
    u = TARGET_OFFSET_S / DURATION_S
    h00 = 2.0 * u**3 - 3.0 * u**2 + 1.0
    h10 = u**3 - 2.0 * u**2 + u
    h01 = -2.0 * u**3 + 3.0 * u**2
    h11 = u**3 - u**2

    position = (
        h00 * start_position
        + h10 * DURATION_S * start_velocity
        + h01 * end_position
        + h11 * DURATION_S * end_velocity
    )

    dh00 = 6.0 * u**2 - 6.0 * u
    dh10 = 3.0 * u**2 - 4.0 * u + 1.0
    dh01 = -6.0 * u**2 + 6.0 * u
    dh11 = 3.0 * u**2 - 2.0 * u

    velocity = (
        dh00 * start_position
        + dh10 * DURATION_S * start_velocity
        + dh01 * end_position
        + dh11 * DURATION_S * end_velocity
    ) / DURATION_S
    return position, velocity


def _hermite_decimal(
    start_position: str,
    start_velocity: str,
    end_position: str,
    end_velocity: str,
) -> tuple[Decimal, Decimal]:
    with localcontext() as context:
        context.prec = 60
        duration = Decimal("600.0")
        target = Decimal("569.416")
        u = target / duration

        h00 = Decimal(2) * u**3 - Decimal(3) * u**2 + Decimal(1)
        h10 = u**3 - Decimal(2) * u**2 + u
        h01 = -Decimal(2) * u**3 + Decimal(3) * u**2
        h11 = u**3 - u**2

        p0 = Decimal(start_position)
        v0 = Decimal(start_velocity)
        p1 = Decimal(end_position)
        v1 = Decimal(end_velocity)

        position = h00 * p0 + h10 * duration * v0 + h01 * p1 + h11 * duration * v1

        dh00 = Decimal(6) * u**2 - Decimal(6) * u
        dh10 = Decimal(3) * u**2 - Decimal(4) * u + Decimal(1)
        dh01 = -Decimal(6) * u**2 + Decimal(6) * u
        dh11 = Decimal(3) * u**2 - Decimal(2) * u

        velocity = (
            dh00 * p0 + dh10 * duration * v0 + dh01 * p1 + dh11 * duration * v1
        ) / duration
    return position, velocity


def test_frozen_repository_records_match_recorded_sha256() -> None:
    for filename, expected_sha256 in FROZEN_HASHES.items():
        assert _sha256(PUBLISHED_DIR / filename) == expected_sha256


def test_frozen_hermite_proof_matches_recorded_sha256() -> None:
    proof_path = DOCS_SATCOM_DIR / "inmarsat_3f1_hermite_mathematical_proof_v1.md"
    assert _sha256(proof_path) == PROOF_SHA256


def test_satellite_state_review_matches_recorded_sha256() -> None:
    review_path = (
        PUBLISHED_DIR / "inmarsat_3f1_satellite_state_method_independent_review_v1.yaml"
    )
    assert _sha256(review_path) == REVIEW_SHA256


def test_provenance_chain_preserves_satellite_review_after_fixture_freeze() -> None:
    chain_path = PUBLISHED_DIR / "satellite_state_provenance_chain.yaml"
    chain = chain_path.read_text(encoding="utf-8")
    fixture_path = PUBLISHED_DIR / "benchmark_fixture.csv"

    for expected_sha256 in FROZEN_HASHES.values():
        assert expected_sha256 in chain
    assert SOURCE_PDF_SHA256 in chain
    assert PROOF_SHA256 in chain
    assert REVIEW_SHA256 in chain
    assert "PASS_FOR_PROGRESS_TO_PERTH_GES" in chain
    assert "benchmark_fixture.csv" in chain
    assert f"status: {PENDING_FIXTURE_STATUS}" in chain
    assert fixture_path.exists()
    assert "status: ADMITTED" not in chain


def test_independent_binary64_reproduction_matches_frozen_target_state() -> None:
    x_state = _hermite_binary64(18_177_500.0, 1.60, 18_178_400.0, 1.50)
    y_state = _hermite_binary64(38_051_700.0, -1.51, 38_050_800.0, -1.58)
    z_state = _hermite_binary64(440_000.0, -81.88, 390_500.0, -83.21)

    reproduced_position = (x_state[0], y_state[0], z_state[0])
    reproduced_velocity = (x_state[1], y_state[1], z_state[1])

    for actual, expected in zip(
        reproduced_position,
        FROZEN_POSITION_M,
        strict=True,
    ):
        assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6)

    for actual, expected in zip(
        reproduced_velocity,
        FROZEN_VELOCITY_M_S,
        strict=True,
    ):
        assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)


def test_high_precision_audit_bounds_binary64_roundoff() -> None:
    x_state = _hermite_decimal("18177500.0", "1.60", "18178400.0", "1.50")
    y_state = _hermite_decimal("38051700.0", "-1.51", "38050800.0", "-1.58")
    z_state = _hermite_decimal("440000.0", "-81.88", "390500.0", "-83.21")

    high_precision_position = (
        float(x_state[0]),
        float(y_state[0]),
        float(z_state[0]),
    )
    high_precision_velocity = (
        float(x_state[1]),
        float(y_state[1]),
        float(z_state[1]),
    )

    for actual, expected in zip(
        high_precision_position,
        FROZEN_POSITION_M,
        strict=True,
    ):
        assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6)

    for actual, expected in zip(
        high_precision_velocity,
        FROZEN_VELOCITY_M_S,
        strict=True,
    ):
        assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=5e-12)
