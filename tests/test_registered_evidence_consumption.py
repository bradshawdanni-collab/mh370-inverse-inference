"""Tests for deterministic L3.0 registered-evidence consumption."""

from typing import Any

import pytest

from mh370_inverse_inference.consumption.gate import consume_registered_evidence
from mh370_inverse_inference.consumption.models import (
    ConsumptionReason,
    ConsumptionStatus,
    EvidenceConsumptionRequest,
    RegisteredEvidenceProjection,
)
from mh370_inverse_inference.consumption.trace_adapter import (
    consumption_result_to_trace,
)
from mh370_inverse_inference.engine.trace import TraceStatus
from mh370_inverse_inference.evidence.registration_models import (
    RegisteredEvidenceRecord,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64


def _registered_record() -> RegisteredEvidenceRecord:
    return RegisteredEvidenceRecord(
        registry_evidence_id=HASH_A,
        evidence_id="evidence-001",
        observation_id="obs-001",
        source_id="src-001",
        evidence_hash=HASH_B,
        validation_hash=HASH_C,
        validation_output_hash=HASH_D,
        validation_operation_hash=HASH_E,
    )


def _projection() -> RegisteredEvidenceProjection:
    return RegisteredEvidenceProjection.from_registered_record(_registered_record())


def _request(
    *,
    expected_id: str = HASH_A,
    expected_contract_version: str = "L3.0",
) -> EvidenceConsumptionRequest:
    return EvidenceConsumptionRequest(
        evidence=_projection(),
        expected_registry_evidence_id=expected_id,
        expected_contract_version=expected_contract_version,
        consumption_policy_version="consumption-1.0.0",
    )


def test_projection_can_only_be_created_from_registered_record() -> None:
    projection_type: Any = RegisteredEvidenceProjection

    with pytest.raises(TypeError):
        projection_type(
            registry_evidence_id=HASH_A,
            evidence_id="evidence-001",
            observation_id="obs-001",
            source_id="src-001",
            evidence_hash=HASH_B,
            validation_hash=HASH_C,
            registration_contract_version="L2.3",
        )

    projection = RegisteredEvidenceProjection.from_registered_record(
        _registered_record()
    )
    assert projection.registry_evidence_id == HASH_A


def test_registered_projection_is_consumed_deterministically() -> None:
    request = _request()

    first = consume_registered_evidence(request)
    second = consume_registered_evidence(request)

    assert first == second
    assert first.status is ConsumptionStatus.ACCEPTED
    assert first.reason_codes == (ConsumptionReason.OK,)
    assert first.accepted_projection is not None
    assert first.accepted_projection.registry_evidence_id == HASH_A


def test_registry_identity_mismatch_fails_closed() -> None:
    result = consume_registered_evidence(_request(expected_id=HASH_B))

    assert result.status is ConsumptionStatus.REJECTED
    assert result.accepted_projection is None
    assert result.reason_codes == (ConsumptionReason.REGISTRY_ID_MISMATCH,)


def test_unsupported_contract_version_fails_closed() -> None:
    result = consume_registered_evidence(_request(expected_contract_version="L3.1"))

    assert result.status is ConsumptionStatus.REJECTED
    assert result.accepted_projection is None
    assert result.reason_codes == (ConsumptionReason.UNSUPPORTED_CONTRACT_VERSION,)


def test_consumption_preserves_identity_without_reconstructing_authority() -> None:
    record = _registered_record()
    projection = RegisteredEvidenceProjection.from_registered_record(record)
    request = EvidenceConsumptionRequest(
        evidence=projection,
        expected_registry_evidence_id=record.registry_evidence_id,
        expected_contract_version="L3.0",
        consumption_policy_version="consumption-1.0.0",
    )

    result = consume_registered_evidence(request)

    assert result.accepted_projection is not None
    assert (
        result.accepted_projection.registry_evidence_id == record.registry_evidence_id
    )
    assert result.accepted_projection.evidence_hash == record.evidence_hash
    assert result.accepted_projection.validation_hash == record.validation_hash
    assert not isinstance(result.accepted_projection, RegisteredEvidenceRecord)


def test_consumption_does_not_mutate_input_projection() -> None:
    request = _request()
    before = request.to_payload()

    consume_registered_evidence(request)

    assert request.to_payload() == before


def test_consumption_result_maps_to_shared_trace_contract() -> None:
    result = consume_registered_evidence(_request())

    trace = consumption_result_to_trace(result, stage_index=5)

    assert trace.stage_id == "L3.0-registered-evidence-consumption"
    assert trace.status is TraceStatus.OK
    assert trace.record_count == 1
    assert trace.input_hash == result.input_hash
    assert trace.output_hash == result.output_hash
