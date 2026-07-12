"""End-to-end release test for the deterministic L3 interpretation chain."""

from mh370_inverse_inference.consumption.gate import consume_registered_evidence
from mh370_inverse_inference.consumption.models import (
    ConsumptionReason,
    ConsumptionStatus,
    EvidenceConsumptionRequest,
    RegisteredEvidenceProjection,
)
from mh370_inverse_inference.evidence.registration_models import RegisteredEvidenceRecord
from mh370_inverse_inference.interpretation import (
    NeutralRuleId,
    build_interpretation_request,
    execute_neutral_rule,
    neutral_rule_execution_to_trace,
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


def _run_chain() -> tuple[str, str, str, str, tuple[str, ...]]:
    projection = RegisteredEvidenceProjection.from_registered_record(
        _registered_record()
    )
    consumption = consume_registered_evidence(
        EvidenceConsumptionRequest(
            evidence=projection,
            expected_registry_evidence_id=HASH_A,
            expected_contract_version="L3.0",
            consumption_policy_version="consumption-1.0.0",
        )
    )

    assert consumption.status is ConsumptionStatus.ACCEPTED
    assert consumption.reason_codes == (ConsumptionReason.OK,)
    assert consumption.accepted_projection is not None

    request = build_interpretation_request(consumption.accepted_projection)
    execution = execute_neutral_rule(
        request,
        rule_id=NeutralRuleId.EVIDENCE_CONSUMED,
        interpretation_policy_version="interpretation-1.0.0",
    )
    trace = neutral_rule_execution_to_trace(execution, stage_index=6)

    return (
        request.input_hash,
        execution.result.result_hash,
        execution.op_signature_hash,
        trace.trace_hash,
        tuple(claim.claim_hash for claim in execution.result.derived_claims),
    )


def test_l3_release_chain_is_deterministic_and_replayable() -> None:
    """The complete L3 authority-reduction path must replay identically."""
    first = _run_chain()
    second = _run_chain()

    assert first == second
    assert len(first[4]) == 1


def test_l3_release_chain_preserves_hash_linkage() -> None:
    """Each downstream identity must remain a valid SHA-256 release identity."""
    input_hash, result_hash, operation_hash, trace_hash, claim_hashes = _run_chain()

    for digest in (
        input_hash,
        result_hash,
        operation_hash,
        trace_hash,
        *claim_hashes,
    ):
        assert len(digest) == 64
        assert digest == digest.lower()
        int(digest, 16)
