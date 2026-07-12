"""Release-freeze tests for the completed deterministic L3 layer."""

import hashlib
import json
from pathlib import Path

from mh370_inverse_inference.interpretation import claim, executor, models, result
from mh370_inverse_inference.interpretation.release import (
    CANONICAL_REPLAY_FIXTURE,
    CANONICAL_REPLAY_FIXTURE_SHA256,
    CONTRACT_VERSIONS,
    INTERPRETATION_RULE_VERSION,
    INTERPRETATION_STAGE_ID,
    L3_RELEASE_STATUS,
    L3_RELEASE_TAG,
    L3_RELEASE_VERSION,
)
from mh370_inverse_inference.interpretation.trace_adapter import STAGE_ID

MANIFEST_PATH = Path("release/l3-release-manifest.json")


def test_l3_contract_versions_are_frozen() -> None:
    assert CONTRACT_VERSIONS == {
        "registered_evidence_consumption": "L3.0",
        "interpretation_request": "L3.1",
        "neutral_derived_claim": "L3.3",
        "interpretation_result": "L3.4",
        "neutral_rule_execution": "L3.5",
        "shared_trace_replay": "L3.6",
    }
    assert models.CONTRACT_VERSION == CONTRACT_VERSIONS["interpretation_request"]
    assert claim.CONTRACT_VERSION == CONTRACT_VERSIONS["neutral_derived_claim"]
    assert result.CONTRACT_VERSION == CONTRACT_VERSIONS["interpretation_result"]
    assert executor.CONTRACT_VERSION == CONTRACT_VERSIONS["neutral_rule_execution"]
    assert executor.RULE_VERSION == INTERPRETATION_RULE_VERSION
    assert STAGE_ID == INTERPRETATION_STAGE_ID


def test_l3_release_manifest_matches_frozen_surface() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_version"] == L3_RELEASE_VERSION
    assert manifest["release_tag"] == L3_RELEASE_TAG
    assert manifest["release_status"] == L3_RELEASE_STATUS
    assert manifest["contract_versions"] == CONTRACT_VERSIONS
    assert manifest["interpretation_rule_version"] == INTERPRETATION_RULE_VERSION
    assert manifest["stage_id"] == INTERPRETATION_STAGE_ID


def test_canonical_l3_replay_fixture_is_hash_locked() -> None:
    fixture_path = Path(CANONICAL_REPLAY_FIXTURE)
    fixture_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()

    assert fixture_hash == CANONICAL_REPLAY_FIXTURE_SHA256

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["canonical_replay_fixture"] == {
        "path": CANONICAL_REPLAY_FIXTURE,
        "sha256": CANONICAL_REPLAY_FIXTURE_SHA256,
    }
