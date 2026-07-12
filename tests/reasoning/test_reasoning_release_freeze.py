"""Release-freeze tests for the completed deterministic L4 layer."""

import hashlib
import json
from pathlib import Path

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.reasoning import application, models, result, trace
from mh370_inverse_inference.reasoning.release import (
    CANONICAL_REPLAY_FIXTURE,
    CANONICAL_REPLAY_FIXTURE_SHA256,
    CONTRACT_VERSIONS,
    L4_RELEASE_STATUS,
    L4_RELEASE_TAG,
    L4_RELEASE_VERSION,
)

MANIFEST_PATH = Path("release/l4-release-manifest.json")


def test_l4_contract_versions_are_frozen() -> None:
    assert CONTRACT_VERSIONS == {
        "constrained_reasoning_request": "L4.0",
        "constrained_reasoning_result": "L4.1",
        "rule_application_record": "L4.2",
        "neutral_reasoning_trace": "L4.3",
    }
    assert models.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "constrained_reasoning_request"
    ]
    assert result.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "constrained_reasoning_result"
    ]
    assert application.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "rule_application_record"
    ]
    assert trace.CONTRACT_VERSION == CONTRACT_VERSIONS["neutral_reasoning_trace"]


def test_l4_release_manifest_matches_frozen_surface() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_version"] == L4_RELEASE_VERSION
    assert manifest["release_tag"] == L4_RELEASE_TAG
    assert manifest["release_status"] == L4_RELEASE_STATUS
    assert manifest["contract_versions"] == CONTRACT_VERSIONS
    assert manifest["canonical_replay_fixture"] == {
        "path": CANONICAL_REPLAY_FIXTURE,
        "sha256": CANONICAL_REPLAY_FIXTURE_SHA256,
    }


def test_canonical_l4_replay_fixture_is_hash_locked() -> None:
    fixture_path = Path(CANONICAL_REPLAY_FIXTURE)
    fixture_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()

    assert fixture_hash == CANONICAL_REPLAY_FIXTURE_SHA256


def test_canonical_l4_replay_fixture_hashes_replay() -> None:
    fixture = json.loads(Path(CANONICAL_REPLAY_FIXTURE).read_text(encoding="utf-8"))

    request = fixture["request"]
    assert sha256_payload(request["canonical_payload"]) == request["request_hash"]

    reasoning_result = fixture["result"]
    assert (
        sha256_payload(reasoning_result["canonical_payload"])
        == reasoning_result["result_hash"]
    )

    for record in fixture["rule_application_records"]:
        assert sha256_payload(record["canonical_payload"]) == record["record_hash"]

    reasoning_trace = fixture["trace"]
    assert (
        sha256_payload(reasoning_trace["canonical_payload"])
        == reasoning_trace["trace_hash"]
    )
