from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_V1_PATH = (
    REPO_ROOT / "data" / "governance" / "layer_namespace_registry_v1.json"
)
REGISTRY_V2_PATH = (
    REPO_ROOT / "data" / "governance" / "layer_namespace_registry_v2.json"
)

FROZEN_L5 = {
    "L5.0": "HypothesisEvaluationRequest",
    "L5.1": "HypothesisDefinition",
    "L5.2": "EvidenceHypothesisRelationRecord",
    "L5.3": "HypothesisEvaluationResult",
    "L5.4": "HypothesisEvaluationTrace",
    "L5.5": "ReleaseFreeze",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_hash(registry: dict[str, Any]) -> str:
    payload = {key: value for key, value in registry.items() if key != "registry_hash"}
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _namespace_map(items: list[dict[str, Any]]) -> dict[str, str]:
    return {item["namespace"]: item["name"] for item in items}


def _validate_registry_v2(registry: dict[str, Any]) -> None:
    frozen = registry["frozen_namespaces"]["contracts"]
    canonical = registry["canonical_namespaces"]
    frozen_ids = [item["namespace"] for item in frozen]
    canonical_ids = [item["namespace"] for item in canonical]

    if len(frozen_ids) != len(set(frozen_ids)):
        raise ValueError("duplicate frozen namespace identifier")
    if len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("duplicate canonical namespace identifier")
    if _namespace_map(frozen) != FROZEN_L5:
        raise ValueError("frozen L5 namespace mapping changed")
    if any(identifier.startswith("L5.") for identifier in canonical_ids):
        raise ValueError("evidence-domain namespace cannot use frozen L5")

    ed1_2 = next(
        (item for item in canonical if item["namespace"] == "ED1.2"),
        None,
    )
    if ed1_2 is None:
        raise ValueError("ED1.2 canonical namespace is required")
    if ed1_2["status"] != "PROPOSED":
        raise ValueError("ED1.2 must remain PROPOSED pending admission")
    if ed1_2["authority"] != "NONE_UNTIL_FINAL_ADMISSION":
        raise ValueError("ED1.2 cannot have authority before final admission")
    if registry["reserved_next_namespace"] is not None:
        raise ValueError("no namespace beyond ED1.2 is reserved")


def test_registry_v2_hash_reproduces_deterministically() -> None:
    registry = _load(REGISTRY_V2_PATH)

    assert registry["registry_hash"] == _canonical_hash(registry)
    assert _canonical_hash(registry) == _canonical_hash(copy.deepcopy(registry))


def test_registry_v2_preserves_admitted_v1_identity() -> None:
    registry_v1 = _load(REGISTRY_V1_PATH)
    registry_v2 = _load(REGISTRY_V2_PATH)

    assert registry_v1["registry_hash"] == _canonical_hash(registry_v1)
    assert registry_v1["admission_state"] == "ADMITTED"
    assert registry_v2["source_registry"] == {
        "admission_state": "ADMITTED",
        "path": "data/governance/layer_namespace_registry_v1.json",
        "registry_hash": registry_v1["registry_hash"],
    }


def test_registry_v2_preserves_frozen_l5_mapping() -> None:
    registry = _load(REGISTRY_V2_PATH)
    frozen = registry["frozen_namespaces"]

    assert frozen["release"] == "l5-v1.0.0"
    assert frozen["preservation_status"] == "FROZEN_UNCHANGED"
    assert _namespace_map(frozen["contracts"]) == FROZEN_L5


def test_ed1_0_and_ed1_1_identities_are_unchanged() -> None:
    registry_v1 = _load(REGISTRY_V1_PATH)
    registry_v2 = _load(REGISTRY_V2_PATH)
    v1 = {item["namespace"]: item for item in registry_v1["canonical_namespaces"]}
    v2 = {item["namespace"]: item for item in registry_v2["canonical_namespaces"]}

    assert v2["ED1.0"] == v1["ED1.0"]
    assert v2["ED1.1"] == v1["ED1.1"]


def test_ed1_2_is_proposed_without_authority() -> None:
    registry = _load(REGISTRY_V2_PATH)
    canonical = {item["namespace"]: item for item in registry["canonical_namespaces"]}
    ed1_2 = canonical["ED1.2"]

    assert registry["admission_state"] == "PROPOSED"
    assert registry["disposition"] == "PENDING_CI"
    assert ed1_2 == {
        "authority": "NONE_UNTIL_FINAL_ADMISSION",
        "contract_version": "EVIDENCE-DOMAIN-INTEGRATION-REQUEST-1",
        "existing_identities_preserved": True,
        "implementation": "src/mh370_inverse_inference/evidence/integration_request.py",
        "name": "EvidenceDomainIntegrationRequest",
        "namespace": "ED1.2",
        "status": "PROPOSED",
    }


def test_no_namespace_beyond_ed1_2_is_reserved() -> None:
    registry = _load(REGISTRY_V2_PATH)

    assert registry["reserved_next_namespace"] is None
    assert "NO_INTEGRATION_RESULT" in registry["scope_exclusions"]
    assert "NO_RUNTIME_AUTHORITY" in registry["scope_exclusions"]


def test_registry_v2_rejects_duplicate_canonical_namespace() -> None:
    registry = _load(REGISTRY_V2_PATH)
    registry["canonical_namespaces"].append(
        copy.deepcopy(registry["canonical_namespaces"][0])
    )

    with pytest.raises(
        ValueError,
        match="duplicate canonical namespace identifier",
    ):
        _validate_registry_v2(registry)


def test_registry_v2_rejects_frozen_l5_2_remap() -> None:
    registry = _load(REGISTRY_V2_PATH)
    frozen = registry["frozen_namespaces"]["contracts"]
    l5_2 = next(item for item in frozen if item["namespace"] == "L5.2")
    l5_2["name"] = "EvidenceDomainIntegrationRequest"

    with pytest.raises(ValueError, match="frozen L5 namespace mapping changed"):
        _validate_registry_v2(registry)


def test_registry_v2_rejects_premature_ed1_2_authority() -> None:
    registry = _load(REGISTRY_V2_PATH)
    ed1_2 = next(
        item
        for item in registry["canonical_namespaces"]
        if item["namespace"] == "ED1.2"
    )
    ed1_2["authority"] = "ACTIVE"

    with pytest.raises(ValueError, match="cannot have authority"):
        _validate_registry_v2(registry)
