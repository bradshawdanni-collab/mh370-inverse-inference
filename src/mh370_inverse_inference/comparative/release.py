"""Frozen public release surface for the completed L6 comparative layer."""

from __future__ import annotations

from typing import Final

L6_RELEASE_VERSION: Final = "1.0.0"
L6_RELEASE_TAG: Final = "l6-v1.0.0"
L6_RELEASE_STATUS: Final = "FROZEN"

CONTRACT_VERSIONS: Final[dict[str, str]] = {
    "comparative_assessment_request": "L6.0",
    "comparative_assessment_record": "L6.1",
    "comparative_assessment_result": "L6.2",
    "comparative_assessment_trace": "L6.3",
}

CANONICAL_REPLAY_FIXTURE: Final = (
    "tests/fixtures/comparative/l6_4_release_case_001.json"
)
CANONICAL_REPLAY_FIXTURE_SHA256: Final = (
    "8227573931afe760cdd394a531b21d17608384a82518f8026a624f3f56b00e52"
)

__all__ = [
    "CANONICAL_REPLAY_FIXTURE",
    "CANONICAL_REPLAY_FIXTURE_SHA256",
    "CONTRACT_VERSIONS",
    "L6_RELEASE_STATUS",
    "L6_RELEASE_TAG",
    "L6_RELEASE_VERSION",
]
