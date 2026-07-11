"""Pure deterministic queries over immutable L2.4 registry snapshots."""

from __future__ import annotations

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.evidence.registry_models import (
    CONTRACT_VERSION,
    OPERATION,
    EvidenceRegistryReason,
    EvidenceRegistryRequest,
    EvidenceRegistryResult,
    EvidenceRegistrySnapshot,
    EvidenceRegistryStatus,
    RegisteredEvidenceLookup,
)


def contains(
    snapshot: EvidenceRegistrySnapshot,
    registry_evidence_id: str,
) -> bool:
    """Return whether the immutable snapshot contains one registry identity."""
    return any(
        record.registry_evidence_id == registry_evidence_id
        for record in snapshot.records
    )


def list_by_observation(
    snapshot: EvidenceRegistrySnapshot,
    observation_id: str,
) -> tuple[RegisteredEvidenceLookup, ...]:
    """Return a canonically ordered projection for one observation lineage."""
    return tuple(
        RegisteredEvidenceLookup.from_record(record)
        for record in snapshot.records
        if record.observation_id == observation_id
    )


def lookup(request: EvidenceRegistryRequest) -> EvidenceRegistryResult:
    """Look up one registered identity without mutating the snapshot."""
    matched = next(
        (
            record
            for record in request.snapshot.records
            if record.registry_evidence_id == request.registry_evidence_id
        ),
        None,
    )
    found = matched is not None
    status = EvidenceRegistryStatus.FOUND if found else EvidenceRegistryStatus.NOT_FOUND
    reason_codes = (
        (EvidenceRegistryReason.OK,)
        if found
        else (EvidenceRegistryReason.EVIDENCE_NOT_REGISTERED,)
    )
    projection = (
        None if matched is None else RegisteredEvidenceLookup.from_record(matched)
    )

    input_hash = sha256_payload(request.to_payload())
    op_signature_hash = sha256_payload(
        {
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
            "registry_policy_version": request.registry_policy_version,
        }
    )
    output_hash = sha256_payload(
        {
            "lookup": None if projection is None else projection.to_payload(),
            "reason_codes": [reason.value for reason in reason_codes],
            "snapshot_hash": request.snapshot.snapshot_hash,
            "status": status.value,
        }
    )

    return EvidenceRegistryResult(
        status=status,
        reason_codes=reason_codes,
        lookup=projection,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        snapshot_hash=request.snapshot.snapshot_hash,
        registry_policy_version=request.registry_policy_version,
    )
