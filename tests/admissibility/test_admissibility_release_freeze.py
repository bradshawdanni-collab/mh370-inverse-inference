"""Release-freeze tests for the completed deterministic L7 layer."""

import hashlib
import json
from pathlib import Path

from mh370_inverse_inference.admissibility import record, request, result, trace
from mh370_inverse_inference.admissibility.release import (
    CANONICAL_REPLAY_FIXTURE,
    CANONICAL_REPLAY_FIXTURE_SHA256,
    CONTRACT_VERSIONS,
    L7_RELEASE_STATUS,
    L7_RELEASE_TAG,
    L7_RELEASE_VERSION,
)
from mh370_inverse_inference.engine.hashing import sha256_payload

MANIFEST_PATH = Path("release/l7-release-manifest.json")


def test_l7_contract_versions_are_frozen() -> None:
    assert CONTRACT_VERSIONS == {
        "admissibility_decision_request": "L7.0",
        "admissibility_decision_record": "L7.1",
        "admissibility_decision_result": "L7.2",
        "admissibility_decision_trace": "L7.3",
    }
    assert (
        request.CONTRACT_VERSION
        == CONTRACT_VERSIONS["admissibility_decision_request"]
    )
    assert (
        record.CONTRACT_VERSION
        == CONTRACT_VERSIONS["admissibility_decision_record"]
    )
    assert (
        result.CONTRACT_VERSION
        == CONTRACT_VERSIONS["admissibility_decision_result"]
    )
    assert (
        trace.CONTRACT_VERSION
        == CONTRACT_VERSIONS["admissibility_decision_trace"]
    )


def test_l7_release_manifest_matches_frozen_surface() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_version"] == L7_RELEASE_VERSION
    assert manifest["release_tag"] == L7_RELEASE_TAG
    assert manifest["release_status"] == L7_RELEASE_STATUS
    assert manifest["contract_versions"] == CONTRACT_VERSIONS
    assert manifest["canonical_replay_fixture"] == {
        "path": CANONICAL_REPLAY_FIXTURE,
        "sha256": CANONICAL_REPLAY_FIXTURE_SHA256,
    }


def test_canonical_l7_replay_fixture_is_hash_locked() -> None:
    fixture_path = Path(CANONICAL_REPLAY_FIXTURE)
    fixture_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()

    assert fixture_hash == CANONICAL_REPLAY_FIXTURE_SHA256


def test_canonical_l7_replay_fixture_hashes_replay() -> None:
    fixture = json.loads(Path(CANONICAL_REPLAY_FIXTURE).read_text(encoding="utf-8"))

    admissibility_request = fixture["request"]
    assert (
        sha256_payload(admissibility_request["canonical_payload"])
        == admissibility_request["request_hash"]
    )

    for admissibility_record in fixture["records"]:
        assert (
            sha256_payload(admissibility_record["canonical_payload"])
            == admissibility_record["record_hash"]
        )

    admissibility_result = fixture["result"]
    assert (
        sha256_payload(admissibility_result["canonical_payload"])
        == admissibility_result["result_hash"]
    )

    admissibility_trace = fixture["trace"]
    assert (
        sha256_payload(admissibility_trace["canonical_payload"])
        == admissibility_trace["trace_hash"]
    )
