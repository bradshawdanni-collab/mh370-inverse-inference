from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = (
    REPO_ROOT / "data" / "governance" / "layer_namespace_registry_v1.json"
)
VALIDATION_ARTIFACT_PATH = (
    REPO_ROOT / "data" / "evidence" / "l5_validation_v1.json"
)
VALIDATION_ARTIFACT_SHA256 = (
    "ea9579227f162614e01eb2fb3f6281c58b7aaa6f7570721d7d99742a31c1577e"
)

FROZEN_L5 = {
    "L5.0": "HypothesisEvaluationRequest",
    "L5.1": "HypothesisDefinition",
    "L5.2": "EvidenceHypothesisRelationRecord",
    "L5.3": "HypothesisEvaluationResult",
    "L5.4": "HypothesisEvaluationTrace",
    "L5.5": "ReleaseFreeze",
}


def _load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _canonical_registry_hash(registry: dict[str, Any]) -> str:
    payload = {key: value for key, value in registry.items() if key != "registry_hash"}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_registry(registry: dict[str, Any]) -> None:
    frozen = registry["frozen_namespaces"]["contracts"]
    canonical = registry["canonical_namespaces"]

    frozen_ids = [item["namespace"] for item in frozen]
    canonical_ids = [item["namespace"] for item in canonical]

    if len(frozen_ids) != len(set(frozen_ids)):
        raise ValueError("duplicate frozen namespace identifier")
    if len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("duplicate canonical namespace identifier")

    frozen_map = {item["namespace"]: item["name"] for item in frozen}
    if frozen_map != FROZEN_L5:
        raise ValueError("frozen L5 namespace mapping changed")
    if any(identifier.startswith("L5.") for identifier in canonical_ids):
        raise ValueError("evidence-domain namespace cannot use frozen L5")

    reserved = registry["reserved_next_namespace"]
    if reserved["namespace"] in canonical_ids:
        raise ValueError("reserved namespace cannot be implemented")
    if reserved["implementation_status"] != "NOT_IMPLEMENTED":
        raise ValueError("reserved namespace must remain unimplemented")


def test_registry_hash_reproduces_deterministically() -> None:
    registry = _load_registry()

    assert registry["registry_hash"] == _canonical_registry_hash(registry)
    assert _canonical_registry_hash(registry) == _canonical_registry_hash(
        copy.deepcopy(registry)
    )


def test_namespace_identifiers_are_unique() -> None:
    registry = _load_registry()
    _validate_registry(registry)

    frozen_ids = [
        item["namespace"]
        for item in registry["frozen_namespaces"]["contracts"]
    ]
    canonical_ids = [
        item["namespace"] for item in registry["canonical_namespaces"]
    ]

    assert len(frozen_ids) == len(set(frozen_ids))
    assert len(canonical_ids) == len(set(canonical_ids))


def test_frozen_l5_release_mapping_is_preserved() -> None:
    registry = _load_registry()
    frozen = registry["frozen_namespaces"]

    assert frozen["release"] == "l5-v1.0.0"
    assert frozen["preservation_status"] == "FROZEN_UNCHANGED"
    assert {item["namespace"]: item["name"] for item in frozen["contracts"]} == (
        FROZEN_L5
    )


def test_ed1_contract_versions_are_preserved() -> None:
    registry = _load_registry()
    canonical = {
        item["namespace"]: item for item in registry["canonical_namespaces"]
    }

    assert canonical["ED1.0"]["contract_version"] == (
        "EVIDENCE-DOMAIN-ADMISSION-1"
    )
    assert canonical["ED1.1"]["contract_version"] == (
        "EVIDENCE-DOMAIN-VALIDATION-1"
    )
    assert canonical["ED1.0"]["existing_identities_preserved"] is True
    assert canonical["ED1.1"]["existing_identities_preserved"] is True


def test_historical_aliases_are_non_authoritative() -> None:
    registry = _load_registry()
    aliases = registry["historical_aliases"]

    assert {item["alias"]: item["canonical_namespace"] for item in aliases} == {
        "L5.0": "ED1.0",
        "L5.1": "ED1.1",
    }
    assert all(
        item["classification"] == "LEGACY_COLLIDING_ALIAS"
        for item in aliases
    )
    assert all(item["authoritative"] is False for item in aliases)
    assert all(
        item["retention"] == "HISTORICAL_TRACEABILITY_ONLY"
        for item in aliases
    )


def test_canonical_evidence_namespaces_do_not_use_l5() -> None:
    registry = _load_registry()

    assert all(
        not item["namespace"].startswith("L5.")
        for item in registry["canonical_namespaces"]
    )


def test_ed1_2_is_reserved_and_unimplemented() -> None:
    registry = _load_registry()
    reserved = registry["reserved_next_namespace"]

    assert reserved == {
        "implementation_status": "NOT_IMPLEMENTED",
        "name": "EvidenceDomainIntegrationRequest",
        "namespace": "ED1.2",
        "reservation_effect": "NO_IMPLEMENTATION_OR_AUTHORITY",
    }


def test_duplicate_namespace_identifier_is_rejected() -> None:
    registry = _load_registry()
    registry["canonical_namespaces"].append(
        copy.deepcopy(registry["canonical_namespaces"][0])
    )

    with pytest.raises(
        ValueError,
        match="duplicate canonical namespace identifier",
    ):
        _validate_registry(registry)


def test_frozen_l5_2_remap_is_rejected() -> None:
    registry = _load_registry()
    frozen = registry["frozen_namespaces"]["contracts"]
    l5_2 = next(item for item in frozen if item["namespace"] == "L5.2")
    l5_2["name"] = "EvidenceDomainIntegrationRequest"

    with pytest.raises(ValueError, match="frozen L5 namespace mapping changed"):
        _validate_registry(registry)


def test_existing_admitted_validation_artifact_is_unchanged() -> None:
    digest = hashlib.sha256(VALIDATION_ARTIFACT_PATH.read_bytes()).hexdigest()

    assert digest == VALIDATION_ARTIFACT_SHA256
