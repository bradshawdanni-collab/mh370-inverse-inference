"""Frozen public release surface for the completed L5 hypothesis layer."""

from __future__ import annotations

from typing import Final

L5_RELEASE_VERSION: Final = "1.0.0"
L5_RELEASE_TAG: Final = "l5-v1.0.0"
L5_RELEASE_STATUS: Final = "FROZEN"

CONTRACT_VERSIONS: Final[dict[str, str]] = {
    "hypothesis_evaluation_request": "L5.0",
    "hypothesis_definition": "L5.1",
    "evidence_hypothesis_relation_record": "L5.2",
    "hypothesis_evaluation_result": "L5.3",
    "hypothesis_evaluation_trace": "L5.4",
}

CANONICAL_REPLAY_FIXTURE: Final = "tests/fixtures/hypothesis/l5_5_release_case_001.json"
CANONICAL_REPLAY_FIXTURE_SHA256: Final = (
    "92b8cce6ee078b636f91b2556a160fbdcbde45cb6d86ff29814923b7aab3ef8d"
)

__all__ = [
    "CANONICAL_REPLAY_FIXTURE",
    "CANONICAL_REPLAY_FIXTURE_SHA256",
    "CONTRACT_VERSIONS",
    "L5_RELEASE_STATUS",
    "L5_RELEASE_TAG",
    "L5_RELEASE_VERSION",
]
