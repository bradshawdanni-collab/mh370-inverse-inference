"""Independent reproduction checks for the frozen #172 satellite-state chain."""

from __future__ import annotations

import hashlib
from decimal import Decimal, getcontext
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_DIR = REPO_ROOT / "data" / "satcom" / "published"

ENDPOINTS_SHA256 = "835c5a93ca9af0c618bb692404a8af59a079aa08af3188df0abcaa3b515eebbc"
TRANSFORM_SHA256 = "ea135509fc6d1dcc9e2f5dad07780ad74e976337a02ba073351f243c1b79ee82"
TARGET_STATE_SHA256 = "c61f400c8b27b07b3acc57701d958068ee8cbb2654a5e325e3f2d0f0cb166452"
SOURCE_PDF_SHA256 = "2ff0f10c1cf0bad299e5398ad9019a113963f6a5bd86b96bf4d04d330bc08028"

FROZEN_HASHES = {
    "inmarsat_3f1_table4_endpoints.yaml": ENDPOINTS_SHA256,
    "inmarsat_3f1_hermite_transform_v1.yaml": TRANSFORM_SHA256,
    "inmarsat_3f1_target_state_20140308T001929416Z.yaml": TARGET_STATE_SHA256,
}

START_POSITION_M = (18_177_500.0, 38_051_700.0, 440_000.0)
START_VELOCITY_M_S = (1.60, -1.51, -81.88)
END_POSITION_M = (18_178_400.0, 38_050_800.0, 390_500.0)
END_VELOCITY_M_S = (1.50, -1.58, -83.21)
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


def _hermite_component_binary64(
    *,
    start_position: float,
    start_velocity: float,
    end_position: float,
    end_velocity: float,
) -> tuple[float, float]:
    """Independent scalar binary64 implementation; does not call production code."""

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


def _hermite_component_decimal(
    *,
    start_position: str,
    start_velocity: str,
    end_position: str,
    end_velocity: str,
) -> tuple[Decimal, Decimal]:
    """High-precision audit implementation to bound binary64 round-off."""

    getcontext().prec = 60
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


def test_provenance_chain_references_frozen_hashes_and_source_hash() -> None:
    chain = (PUBLISHED_DIR / "satellite_state_provenance_chain.yaml").read_text(
        encoding="utf-8"
    )

    for expected_sha256 in FROZEN_HASHES.values():
        assert expected_sha256 in chain
    assert SOURCE_PDF_SHA256 in chain
    assert "benchmark_fixture.csv" in chain
    assert "status: NOT_CREATED" in chain


def test_independent_binary64_reproduction_matches_frozen_target_state() -> None:
    reproduced = tuple(
        _hermite_component_binary64(
            start_position=start_position,
            start_velocity=start_velocity,
            end_position=end_position,
            end_velocity=end_velocity,
        )
        for start_position, start_velocity, end_position, end_velocity in zip(
            START_POSITION_M,
            START_VELOCITY_M_S,
            END_POSITION_M,
            END_VELOCITY_M_S,
            strict=True,
        )
    )

    reproduced_position = tuple(component[0] for component in reproduced)
    reproduced_velocity = tuple(component[1] for component in reproduced)

    assert reproduced_position == pytest.approx(FROZEN_POSITION_M, abs=1e-6)
    assert reproduced_velocity == pytest.approx(FROZEN_VELOCITY_M_S, abs=1e-12)


def test_high_precision_audit_bounds_binary64_roundoff() -> None:
    decimal_inputs = (
        ("18177500.0", "1.60", "18178400.0", "1.50"),
        ("38051700.0", "-1.51", "38050800.0", "-1.58"),
        ("440000.0", "-81.88", "390500.0", "-83.21"),
    )

    high_precision = tuple(
        _hermite_component_decimal(
            start_position=start_position,
            start_velocity=start_velocity,
            end_position=end_position,
            end_velocity=end_velocity,
        )
        for start_position, start_velocity, end_position, end_velocity in decimal_inputs
    )

    high_precision_position = tuple(float(component[0]) for component in high_precision)
    high_precision_velocity = tuple(float(component[1]) for component in high_precision)

    assert FROZEN_POSITION_M == pytest.approx(high_precision_position, abs=1e-6)
    assert FROZEN_VELOCITY_M_S == pytest.approx(high_precision_velocity, abs=5e-12)
