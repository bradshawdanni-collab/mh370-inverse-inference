"""Release-freeze tests for the completed deterministic L6 layer."""

import hashlib
import json
from pathlib import Path

from mh370_inverse_inference.comparative import record, request, result, trace
from mh370_inverse_inference.comparative.release import (
    CANONICAL_REPLAY_FIXTURE,
    CANONICAL_REPLAY_FIXTURE_SHA256,
    CONTRACT_VERSIONS,
    L6_RELEASE_STATUS,
    L6_RELEASE_TAG,
    L6_RELEASE_VERSION,
)
from mh370_inverse_inference.engine.hashing import sha256_payload

MANIFEST_PATH = Path("release/l6-release-manifest.json")


def test_l6_contract_versions_are_frozen() -> None:
    assert CONTRACT_VERSIONS == {
        "comparative_assessment_request": "L6.0",
        "comparative_assessment_record": "L6.1",
        "comparative_assessment_result": "L6.2",
        "comparative_assessment_trace": "L6.3",
    }
    assert request.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "comparative_assessment_request"
    ]
    assert record.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "comparative_assessment_record"
    ]
    assert result.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "comparative_assessment_result"
    ]
    assert trace.CONTRACT_VERSION == CONTRACT_VERSIONS[
        "comparative_assessment_trace"
    ]


def test_l6_release_manifest_matches_frozen_surface() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["release_version"] == L6_RELEASE_VERSION
    assert manifest["release_tag"] == L6_RELEASE_TAG
    assert manifest["release_status"] == L6_RELEASE_STATUS
    assert manifest["contract_versions"] == CONTRACT_VERSIONS
    assert manifest["canonical_replay_fixture"] == {
        "path": CANONICAL_REPLAY_FIXTURE,
        "sha256": CANONICAL_REPLAY_FIXTURE_SHA256,
    }


def test_canonical_l6_replay_fixture_is_hash_locked() -> None:
    fixture_path = Path(CANONICAL_REPLAY_FIXTURE)
    fixture_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()

    assert fixture_hash == CANONICAL_REPLAY_FIXTURE_SHA256


def test_canonical_l6_replay_fixture_hashes_replay() -> None:
    fixture = json.loads(Path(CANONICAL_REPLAY_FIXTURE).read_text(encoding="utf-8"))

    comparative_request = fixture["request"]
    assert (
        sha256_payload(comparative_request["canonical_payload"])
        == comparative_request["request_hash"]
    )

    for comparative_record in fixture["records"]:
        assert (
            sha256_payload(comparative_record["canonical_payload"])
            == comparative_record["record_hash"]
        )

    comparative_result = fixture["result"]
    assert (
        sha256_payload(comparative_result["canonical_payload"])
        == comparative_result["result_hash"]
    )

    comparative_trace = fixture["trace"]
    assert (
        sha256_payload(comparative_trace["canonical_payload"])
        == comparative_trace["trace_hash"]
    )
