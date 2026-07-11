"""Tests for deterministic L2.4 evidence registry queries."""

from dataclasses import replace

import pytest

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.engine.trace import TraceStatus
from mh370_inverse_inference.evidence.registration_models import (
    RegisteredEvidenceRecord,
)
from mh370_inverse_inference.evidence.registry import (
    contains,
    list_by_observation,
    lookup,
)
from mh370_inverse_inference.evidence.registry_models import (
    EvidenceRegistryReason,
    EvidenceRegistryRequest,
    EvidenceRegistrySnapshot,
    EvidenceRegistryStatus,
    snapshot_identity_payload,
)
from mh370_inverse_inference.evidence.registry_trace_adapter import (
    registry_result_to_trace,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _record(registry_id: str, evidence_id: str, observation_id: str):
    return RegisteredEvidenceRecord(
        registry_evidence_id=registry_id,
        evidence_id=evidence_id,
        observation_id=observation_id,
        source_id="src-001",
        evidence_hash=HASH_A,
        validation_hash=HASH_B,
        validation_output_hash=HASH_C,
        validation_operation_hash=HASH_D,
    )


def _snapshot(
    records: tuple[RegisteredEvidenceRecord, ...],
) -> EvidenceRegistrySnapshot:
    return EvidenceRegistrySnapshot(
        records=records,
        snapshot_hash=sha256_payload(snapshot_identity_payload(records)),
    )


def _request(snapshot: EvidenceRegistrySnapshot, registry_id: str):
    return EvidenceRegistryRequest(
        snapshot=snapshot,
        registry_evidence_id=registry_id,
        registry_policy_version="registry-query-1.0.0",
    )


def test_lookup_is_deterministic_and_found() -> None:
    snapshot = _snapshot((_record(HASH_A, "evidence-001", "obs-001"),))
    request = _request(snapshot, HASH_A)

    first = lookup(request)
    second = lookup(request)

    assert first == second
    assert first.status is EvidenceRegistryStatus.FOUND
    assert first.reason_codes == (EvidenceRegistryReason.OK,)
    assert first.lookup is not None
    assert first.lookup.registry_evidence_id == HASH_A


def test_missing_identity_fails_closed_without_exception() -> None:
    snapshot = _snapshot((_record(HASH_A, "evidence-001", "obs-001"),))

    result = lookup(_request(snapshot, HASH_B))

    assert result.status is EvidenceRegistryStatus.NOT_FOUND
    assert result.reason_codes == (EvidenceRegistryReason.EVIDENCE_NOT_REGISTERED,)
    assert result.lookup is None


def test_contains_is_pure_and_deterministic() -> None:
    snapshot = _snapshot((_record(HASH_A, "evidence-001", "obs-001"),))
    before = snapshot.to_payload()

    assert contains(snapshot, HASH_A)
    assert not contains(snapshot, HASH_B)
    assert snapshot.to_payload() == before


def test_list_by_observation_uses_canonical_registry_order() -> None:
    records = (
        _record(HASH_A, "evidence-001", "obs-001"),
        _record(HASH_B, "evidence-002", "obs-001"),
        _record(HASH_C, "evidence-003", "obs-002"),
    )
    snapshot = _snapshot(records)

    results = list_by_observation(snapshot, "obs-001")

    assert tuple(item.registry_evidence_id for item in results) == (HASH_A, HASH_B)


def test_snapshot_rejects_noncanonical_order() -> None:
    records = (
        _record(HASH_B, "evidence-002", "obs-001"),
        _record(HASH_A, "evidence-001", "obs-001"),
    )
    snapshot_hash = sha256_payload(snapshot_identity_payload(records))

    with pytest.raises(ValueError, match="ordered"):
        EvidenceRegistrySnapshot(records=records, snapshot_hash=snapshot_hash)


def test_snapshot_rejects_duplicate_registry_ids() -> None:
    first = _record(HASH_A, "evidence-001", "obs-001")
    second = replace(first, evidence_id="evidence-002")
    records = (first, second)
    snapshot_hash = sha256_payload(snapshot_identity_payload(records))

    with pytest.raises(ValueError, match="unique"):
        EvidenceRegistrySnapshot(records=records, snapshot_hash=snapshot_hash)


def test_snapshot_hash_is_verified() -> None:
    records = (_record(HASH_A, "evidence-001", "obs-001"),)

    with pytest.raises(ValueError, match="snapshot_hash"):
        EvidenceRegistrySnapshot(records=records, snapshot_hash=HASH_D)


def test_lookup_maps_to_shared_trace_contract() -> None:
    snapshot = _snapshot((_record(HASH_A, "evidence-001", "obs-001"),))
    result = lookup(_request(snapshot, HASH_A))

    trace = registry_result_to_trace(result, stage_index=4)

    assert trace.stage_id == "L2.4-evidence-registry"
    assert trace.status is TraceStatus.OK
    assert trace.record_count == 1
    assert trace.input_hash == result.input_hash
    assert trace.output_hash == result.output_hash
