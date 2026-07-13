"""Release-freeze tests for the completed deterministic L5 layer."""

import hashlib
import json
from pathlib import Path

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.hypothesis import (
    definition,
    relation,
    request,
    result,
    trace,
)
from mh370_inverse_inference.hypothesis.release import (
    CANONICAL_REPLAY_FIXTURE,
    CANONICAL_REPLAY_FIXTURE_SHA256,
    CONTRACT_VERSIONS,
    L5_RELEASE_STATUS,
    L5_RELEASE_TAG,
    L5_RELEASE_VERSION,
)

MANIFEST_PATH = Path("release/l5-release-manifest.json")


def test_l5_contract_versions_are_frozen() -> None:
    assert CONTRACT_VERSIONS == {
        "hypothesis_evaluation_request": "L5.0",
        "hypothesis_definition": "L5.1",
        "evidence_hypothesis_relation_record": "L5.2",
        "hypothesis_evaluation_result": "L5.3",
        "hypothesis_evaluation_trace": "L5.4",
    }
    assert (
        request.CONTRACT_VERSION == CONTRACT_VERSIONS["hypothesis_evaluation_request"]
    )
    assert definition.CONTRACT_VERSION == CONTRACT_VERSIONS["hypothesis_definition"]
    assert (
        relation.CONTRACT_VERSION
        == CONTRACT_VERSIONS["evidence_hypothesis_relation_record"]
    )
    assert result.CONTRACT_VERSION == CONTRACT_VERSIONS["hypothesis_evaluation_result"]
    assert trace.CONTRACT_VERSION == CONTRACT_VERSIONS["hypothesis_evaluation_trace"]


def test_l5_release_manifest_matches_frozen_surface() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_version"] == L5_RELEASE_VERSION
    assert manifest["release_tag"] == L5_RELEASE_TAG
    assert manifest["release_status"] == L5_RELEASE_STATUS
    assert manifest["contract_versions"] == CONTRACT_VERSIONS
    assert manifest["canonical_replay_fixture"] == {
        "path": CANONICAL_REPLAY_FIXTURE,
        "sha256": CANONICAL_REPLAY_FIXTURE_SHA256,
    }


def test_canonical_l5_replay_fixture_is_hash_locked() -> None:
    fixture_path = Path(CANONICAL_REPLAY_FIXTURE)
    fixture_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()

    assert fixture_hash == CANONICAL_REPLAY_FIXTURE_SHA256


def test_canonical_l5_replay_fixture_hashes_replay() -> None:
    fixture = json.loads(Path(CANONICAL_REPLAY_FIXTURE).read_text(encoding="utf-8"))

    evaluation_request = fixture["request"]
    assert (
        sha256_payload(evaluation_request["canonical_payload"])
        == evaluation_request["request_hash"]
    )

    for record in fixture["relation_records"]:
        assert sha256_payload(record["canonical_payload"]) == record["record_hash"]

    evaluation_result = fixture["result"]
    assert (
        sha256_payload(evaluation_result["canonical_payload"])
        == evaluation_result["result_hash"]
    )

    evaluation_trace = fixture["trace"]
    assert (
        sha256_payload(evaluation_trace["canonical_payload"])
        == evaluation_trace["trace_hash"]
    )
