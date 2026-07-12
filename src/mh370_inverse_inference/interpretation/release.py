"""Frozen public release surface for the completed L3 interpretation layer."""

from __future__ import annotations

from typing import Final

L3_RELEASE_VERSION: Final = "1.0.0"
L3_RELEASE_TAG: Final = "l3-v1.0.0"
L3_RELEASE_STATUS: Final = "FROZEN"

CONTRACT_VERSIONS: Final[dict[str, str]] = {
    "registered_evidence_consumption": "L3.0",
    "interpretation_request": "L3.1",
    "neutral_derived_claim": "L3.3",
    "interpretation_result": "L3.4",
    "neutral_rule_execution": "L3.5",
    "shared_trace_replay": "L3.6",
}

INTERPRETATION_RULE_VERSION: Final = "1.0.0"
INTERPRETATION_STAGE_ID: Final = "L3.6-neutral-interpretation-execution"
CANONICAL_REPLAY_FIXTURE: Final = (
    "tests/fixtures/interpretation/l3_6_replay_case_001.json"
)
CANONICAL_REPLAY_FIXTURE_SHA256: Final = (
    "870720bfe668309a0ef8448e64fb6dff1bd2683716257c597faea27c0d2738df"
)

__all__ = [
    "CANONICAL_REPLAY_FIXTURE",
    "CANONICAL_REPLAY_FIXTURE_SHA256",
    "CONTRACT_VERSIONS",
    "INTERPRETATION_RULE_VERSION",
    "INTERPRETATION_STAGE_ID",
    "L3_RELEASE_STATUS",
    "L3_RELEASE_TAG",
    "L3_RELEASE_VERSION",
]
