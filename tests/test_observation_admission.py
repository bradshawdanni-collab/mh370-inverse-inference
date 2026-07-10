"""Tests for deterministic L2.0 observation admission."""

import math

from mh370_inverse_inference.observations.admission import admit_observation
from mh370_inverse_inference.observations.models import (
    AdmissionReason,
    AdmissionStatus,
    ObservationAdmissionRequest,
    ObservationRecord,
    ObservationSource,
    ObservationType,
    ObservationUncertainty,
    ProvenanceStatus,
)
from mh370_inverse_inference.observations.trace_adapter import (
    admission_trace_record,
)

VALID_HASH = "a" * 64


def build_request(
    *,
    observation_type: ObservationType = ObservationType.BTO,
    measured_value: float = 12345.0,
    units: str = "us",
    provenance_status: ProvenanceStatus = ProvenanceStatus.VERIFIED,
) -> ObservationAdmissionRequest:
    uncertainty = ObservationUncertainty(
        standard_uncertainty=20.0,
        confidence_level=0.95,
        uncertainty_model="standard",
        units=units,
    )
    observation = ObservationRecord(
        observation_id="obs-001",
        observation_type=observation_type,
        timestamp_utc="2014-03-08T18:25:27Z",
        measured_value=measured_value,
        units=units,
        source_id="src-001",
        uncertainty=uncertainty,
        model_version="observation-1.0.0",
    )
    source = ObservationSource(
        source_id="src-001",
        source_type="dataset",
        publisher="reference",
        reference_uri="urn:mh370:observation:001",
        retrieved_at_utc="2026-07-10T00:00:00Z",
        content_hash=VALID_HASH,
        provenance_status=provenance_status,
    )
    return ObservationAdmissionRequest(
        observation=observation,
        source=source,
        expected_model_version="observation-1.0.0",
        expected_contract_version="L2.0",
        admission_policy_version="admission-1.0.0",
    )


def test_valid_bto_is_admitted_deterministically() -> None:
    request = build_request()
    first = admit_observation(request)
    second = admit_observation(request)

    assert first == second
    assert first.status is AdmissionStatus.ADMITTED
    assert first.reason_codes == (AdmissionReason.OK,)


def test_bfo_uses_same_admission_engine() -> None:
    result = admit_observation(
        build_request(
            observation_type=ObservationType.BFO,
            measured_value=85.0,
            units="Hz",
        )
    )

    assert result.status is AdmissionStatus.ADMITTED


def test_non_finite_value_is_rejected() -> None:
    result = admit_observation(build_request(measured_value=math.nan))

    assert result.status is AdmissionStatus.REJECTED
    assert AdmissionReason.NON_FINITE_VALUE in result.reason_codes


def test_unverified_provenance_is_quarantined() -> None:
    result = admit_observation(
        build_request(provenance_status=ProvenanceStatus.UNVERIFIED)
    )

    assert result.status is AdmissionStatus.QUARANTINED
    assert result.reason_codes == (AdmissionReason.UNVERIFIED_PROVENANCE,)


def test_trace_mapping_preserves_identity() -> None:
    result = admit_observation(build_request())
    record = admission_trace_record(result, stage_index=4)

    assert record.input_hash == result.input_hash
    assert record.output_hash == result.output_hash
    assert record.op_signature_hash == result.op_signature_hash
    assert record.record_count == 1
    assert record.hypothesis_count is None
    assert record.normalization_error is None
    assert record.pre_normalization_mass is None
