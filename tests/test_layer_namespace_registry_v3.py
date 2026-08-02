from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_V2_PATH = (
    REPO_ROOT / "data" / "governance" / "layer_namespace_registry_v2.json"
)
REGISTRY_V3_PATH = (
    REPO_ROOT / "data" / "governance" / "layer_namespace_registry_v3.json"
)

PROPOSED_CAPABILITIES = (
    "CONSUME_ONE_VALID_ED1_2_REQUEST",
    "VERIFY_REQUEST_HASH_AND_REFERENCED_RECORDS",
    "COMBINE_EVIDENCE_DOMAINS_UNDER_EXPLICIT_INTEGRATION_POLICY",
    "PRESERVE_EACH_DOMAIN_CONTRIBUTION",
    "IDENTIFY_AGREEMENTS_CONFLICTS_AND_UNRESOLVED_GAPS",
    "PRODUCE_DETERMINISTIC_INTEGRATION_RESULT",
    "RECORD_ASSUMPTIONS_EXCLUSIONS_POLICY_IDENTITY_AND_REPLAY_HASHES",
)

PROPOSED_SCOPE_EXCLUSIONS = (
    "NO_HYPOTHESIS_RANKING",
    "NO_TRAJECTORY_RANKING",
    "NO_ENDPOINT_SELECTION",
    "NO_SEARCH_AREA_RECOMMENDATION",
    "NO_LOCATION_CLAIM",
    "NO_L3_MODIFICATION",
    "NO_RUNTIME_EXECUTION",
)

CURRENT_SCOPE_EXCLUSIONS = (
    "NO_ED1_3_IMPLEMENTATION",
    "NO_INTEGRATION_RESULT",
    "NO_EVIDENCE_FUSION",
    "NO_SCORING",
    "NO_WEIGHTING",
    "NO_HYPOTHESIS_RANKING",
    "NO_TRAJECTORY_RANKING",
    "NO_L3_MODIFICATION",
    "NO_ENDPOINT_SELECTION",
    "NO_SEARCH_AREA_RECOMMENDATION",
    "NO_LOCATION_CLAIM",
    "NO_RUNTIME_AUTHORITY",
)


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


def _validate_registry_v3(registry: dict[str, Any]) -> None:
    reservation = registry["reserved_next_namespace"]
    canonical_ids = {item["namespace"] for item in registry["canonical_namespaces"]}

    if registry["admission_state"] != "PROPOSED":
        raise ValueError("registry v3 must remain PROPOSED pending review")
    if registry["disposition"] != "PENDING_CI":
        raise ValueError("registry v3 disposition must remain PENDING_CI")
    if "ED1.3" in canonical_ids:
        raise ValueError("reserved ED1.3 cannot be canonical before implementation")
    if reservation["namespace"] != "ED1.3":
        raise ValueError("reserved namespace must be ED1.3")
    if reservation["name"] != "EvidenceDomainIntegrationResult":
        raise ValueError("reserved ED1.3 name changed")
    if reservation["implementation_status"] != "NOT_IMPLEMENTED":
        raise ValueError("ED1.3 must remain not implemented")
    if reservation["authority_status"] != "NONE_UNTIL_IMPLEMENTED_TESTED_AND_ADMITTED":
        raise ValueError("ED1.3 cannot have authority before admission")
    if reservation["reservation_effect"] != "NO_IMPLEMENTATION_OR_AUTHORITY":
        raise ValueError("ED1.3 reservation effect changed")
    if tuple(reservation["proposed_capabilities"]) != PROPOSED_CAPABILITIES:
        raise ValueError("ED1.3 proposed capabilities changed")
    if tuple(reservation["proposed_scope_exclusions"]) != PROPOSED_SCOPE_EXCLUSIONS:
        raise ValueError("ED1.3 proposed scope exclusions changed")
    if tuple(registry["scope_exclusions"]) != CURRENT_SCOPE_EXCLUSIONS:
        raise ValueError("current no-authority exclusions changed")


def test_registry_v3_hash_reproduces_deterministically() -> None:
    registry = _load(REGISTRY_V3_PATH)

    assert registry["registry_hash"] == _canonical_hash(registry)
    assert _canonical_hash(registry) == _canonical_hash(copy.deepcopy(registry))


def test_registry_v3_preserves_admitted_v2_identity() -> None:
    registry_v2 = _load(REGISTRY_V2_PATH)
    registry_v3 = _load(REGISTRY_V3_PATH)

    assert registry_v2["registry_hash"] == _canonical_hash(registry_v2)
    assert registry_v2["admission_state"] == "ADMITTED"
    assert registry_v3["source_registry"] == {
        "admission_state": "ADMITTED",
        "path": "data/governance/layer_namespace_registry_v2.json",
        "registry_hash": registry_v2["registry_hash"],
    }
    assert registry_v3["canonical_namespaces"] == registry_v2["canonical_namespaces"]
    assert registry_v3["frozen_namespaces"] == registry_v2["frozen_namespaces"]
    assert registry_v3["historical_aliases"] == registry_v2["historical_aliases"]


def test_ed1_3_is_reservation_only() -> None:
    registry = _load(REGISTRY_V3_PATH)
    reservation = registry["reserved_next_namespace"]

    assert registry["registry_version"] == "LAYER-NAMESPACE-REGISTRY-3"
    assert registry["admission_state"] == "PROPOSED"
    assert registry["disposition"] == "PENDING_CI"
    assert reservation["namespace"] == "ED1.3"
    assert reservation["name"] == "EvidenceDomainIntegrationResult"
    assert reservation["proposed_contract_version"] == (
        "EVIDENCE-DOMAIN-INTEGRATION-RESULT-1"
    )
    assert reservation["input_contract"] == "EVIDENCE-DOMAIN-INTEGRATION-REQUEST-1"
    assert reservation["implementation_status"] == "NOT_IMPLEMENTED"
    assert reservation["authority_status"] == (
        "NONE_UNTIL_IMPLEMENTED_TESTED_AND_ADMITTED"
    )
    assert reservation["reservation_effect"] == "NO_IMPLEMENTATION_OR_AUTHORITY"
    assert all(
        item["namespace"] != "ED1.3" for item in registry["canonical_namespaces"]
    )


def test_ed1_3_proposed_boundary_is_exact() -> None:
    registry = _load(REGISTRY_V3_PATH)
    reservation = registry["reserved_next_namespace"]

    assert tuple(reservation["proposed_capabilities"]) == PROPOSED_CAPABILITIES
    assert tuple(reservation["proposed_scope_exclusions"]) == PROPOSED_SCOPE_EXCLUSIONS
    assert tuple(registry["scope_exclusions"]) == CURRENT_SCOPE_EXCLUSIONS


def test_registry_v3_validator_accepts_canonical_proposal() -> None:
    _validate_registry_v3(_load(REGISTRY_V3_PATH))


def test_registry_v3_rejects_ed1_3_implementation() -> None:
    registry = _load(REGISTRY_V3_PATH)
    registry["reserved_next_namespace"]["implementation_status"] = "IMPLEMENTED"

    with pytest.raises(ValueError, match="must remain not implemented"):
        _validate_registry_v3(registry)


def test_registry_v3_rejects_ed1_3_authority() -> None:
    registry = _load(REGISTRY_V3_PATH)
    registry["reserved_next_namespace"][
        "authority_status"
    ] = "INTEGRATION_RESULT_AUTHORITY"

    with pytest.raises(ValueError, match="cannot have authority"):
        _validate_registry_v3(registry)


def test_registry_v3_rejects_premature_canonical_ed1_3() -> None:
    registry = _load(REGISTRY_V3_PATH)
    registry["canonical_namespaces"].append(
        {
            "authority": "INTEGRATION_RESULT_AUTHORITY",
            "contract_version": "EVIDENCE-DOMAIN-INTEGRATION-RESULT-1",
            "existing_identities_preserved": True,
            "implementation": (
                "src/mh370_inverse_inference/evidence/integration_result.py"
            ),
            "name": "EvidenceDomainIntegrationResult",
            "namespace": "ED1.3",
            "status": "PROPOSED",
        }
    )

    with pytest.raises(ValueError, match="cannot be canonical"):
        _validate_registry_v3(registry)


def test_registry_v3_rejects_removed_location_boundary() -> None:
    registry = _load(REGISTRY_V3_PATH)
    exclusions = registry["reserved_next_namespace"]["proposed_scope_exclusions"]
    exclusions.remove("NO_LOCATION_CLAIM")

    with pytest.raises(ValueError, match="proposed scope exclusions changed"):
        _validate_registry_v3(registry)


def test_registry_v3_rejects_current_fusion_authority() -> None:
    registry = _load(REGISTRY_V3_PATH)
    registry["scope_exclusions"].remove("NO_EVIDENCE_FUSION")

    with pytest.raises(ValueError, match="current no-authority exclusions changed"):
        _validate_registry_v3(registry)
