"""Frozen public release surface for the completed L7 admissibility layer."""

from __future__ import annotations

from typing import Final

L7_RELEASE_VERSION: Final = "1.0.0"
L7_RELEASE_TAG: Final = "l7-v1.0.0"
L7_RELEASE_STATUS: Final = "FROZEN"

CONTRACT_VERSIONS: Final[dict[str, str]] = {
    "admissibility_decision_request": "L7.0",
    "admissibility_decision_record": "L7.1",
    "admissibility_decision_result": "L7.2",
    "admissibility_decision_trace": "L7.3",
}

CANONICAL_REPLAY_FIXTURE: Final = (
    "tests/fixtures/admissibility/l7_4_release_case_001.json"
)
CANONICAL_REPLAY_FIXTURE_SHA256: Final = (
    "386b6df436923005da7ddee39f1cac8b58279f483eff101ed05f5ac1a9f676f8"
)

__all__ = [
    "CANONICAL_REPLAY_FIXTURE",
    "CANONICAL_REPLAY_FIXTURE_SHA256",
    "CONTRACT_VERSIONS",
    "L7_RELEASE_STATUS",
    "L7_RELEASE_TAG",
    "L7_RELEASE_VERSION",
]
