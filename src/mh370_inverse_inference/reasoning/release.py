"""Frozen public release surface for the completed L4 reasoning layer."""

from __future__ import annotations

from typing import Final

L4_RELEASE_VERSION: Final = "1.0.0"
L4_RELEASE_TAG: Final = "l4-v1.0.0"
L4_RELEASE_STATUS: Final = "FROZEN"

CONTRACT_VERSIONS: Final[dict[str, str]] = {
    "constrained_reasoning_request": "L4.0",
    "constrained_reasoning_result": "L4.1",
    "rule_application_record": "L4.2",
    "neutral_reasoning_trace": "L4.3",
}

CANONICAL_REPLAY_FIXTURE: Final = (
    "tests/fixtures/reasoning/l4_4_release_case_001.json"
)
CANONICAL_REPLAY_FIXTURE_SHA256: Final = (
    "e3db1b6465491cf1dd99fca2454a219920b77078808af1ef8790305195a559b1"
)

__all__ = [
    "CANONICAL_REPLAY_FIXTURE",
    "CANONICAL_REPLAY_FIXTURE_SHA256",
    "CONTRACT_VERSIONS",
    "L4_RELEASE_STATUS",
    "L4_RELEASE_TAG",
    "L4_RELEASE_VERSION",
]
