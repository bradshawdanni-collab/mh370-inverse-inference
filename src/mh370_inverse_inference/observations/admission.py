"""Pure deterministic observation-admission policy for L2.0."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.observations.models import (
    CONTRACT_VERSION,
    OPERATION,
    AdmissionReason,
    AdmissionStatus,
    ObservationAdmissionRequest,
    ObservationAdmissionResult,
    ObservationType,
    ProvenanceStatus,
)

_EXPECTED_UNITS = {
    ObservationType.BTO: "us",
    ObservationType.BFO: "Hz",
    ObservationType.RADAR_SPEED: "m/s",
    ObservationType.RADAR_HEADING: "deg",
}


def _identity_safe(value: Any) -> Any:
    """Represent invalid non-finite input for deterministic rejection identity."""
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "<nan>"
        return "<positive-infinity>" if value > 0.0 else "<negative-infinity>"
    if isinstance(value, dict):
        return {key: _identity_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_identity_safe(item) for item in value]
    return value


def _valid_utc(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return (
        parsed.utcoffset() is not None
        and parsed.utcoffset().total_seconds() == 0.0
    )


def _reasons(request: ObservationAdmissionRequest) -> tuple[AdmissionReason, ...]:
    observation = request.observation
    source = request.source
    reasons: list[AdmissionReason] = []

    if not _valid_utc(observation.timestamp_utc):
        reasons.append(AdmissionReason.INVALID_TIMESTAMP)
    if not observation.has_finite_value:
        reasons.append(AdmissionReason.NON_FINITE_VALUE)

    expected_units = _EXPECTED_UNITS.get(observation.observation_type)
    if not observation.units.strip():
        reasons.append(AdmissionReason.INVALID_UNITS)
    elif expected_units is not None and observation.units != expected_units:
        reasons.append(AdmissionReason.INVALID_UNITS)

    uncertainty = observation.uncertainty
    standard = uncertainty.standard_uncertainty
    confidence = uncertainty.confidence_level
    if standard is not None and (not math.isfinite(standard) or standard < 0.0):
        reasons.append(AdmissionReason.INVALID_UNCERTAINTY)
    if confidence is not None and (
        not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0
    ):
        reasons.append(AdmissionReason.INVALID_UNCERTAINTY)
    if uncertainty.units != observation.units:
        reasons.append(AdmissionReason.UNIT_MISMATCH)

    if source is None or source.provenance_status is ProvenanceStatus.MISSING:
        reasons.append(AdmissionReason.MISSING_SOURCE)
    else:
        if source.source_id != observation.source_id:
            reasons.append(AdmissionReason.MISSING_SOURCE)
        if not source.has_valid_hash:
            reasons.append(AdmissionReason.INVALID_SOURCE_HASH)
        if source.provenance_status is ProvenanceStatus.UNVERIFIED:
            reasons.append(AdmissionReason.UNVERIFIED_PROVENANCE)

    if observation.model_version != request.expected_model_version:
        reasons.append(AdmissionReason.MODEL_VERSION_MISMATCH)
    if observation.contract_version != request.expected_contract_version:
        reasons.append(AdmissionReason.CONTRACT_VERSION_MISMATCH)

    return tuple(dict.fromkeys(reasons)) or (AdmissionReason.OK,)


def _status(reasons: tuple[AdmissionReason, ...]) -> AdmissionStatus:
    hard_failures = {
        AdmissionReason.INVALID_SCHEMA,
        AdmissionReason.INVALID_TIMESTAMP,
        AdmissionReason.NON_FINITE_VALUE,
        AdmissionReason.INVALID_UNITS,
        AdmissionReason.UNIT_MISMATCH,
        AdmissionReason.INVALID_UNCERTAINTY,
        AdmissionReason.INVALID_SOURCE_HASH,
        AdmissionReason.UNSUPPORTED_OBSERVATION_TYPE,
        AdmissionReason.MODEL_VERSION_MISMATCH,
        AdmissionReason.CONTRACT_VERSION_MISMATCH,
    }
    if any(reason in hard_failures for reason in reasons):
        return AdmissionStatus.REJECTED
    quarantine_reasons = {
        AdmissionReason.MISSING_SOURCE,
        AdmissionReason.UNVERIFIED_PROVENANCE,
    }
    if any(reason in quarantine_reasons for reason in reasons):
        return AdmissionStatus.QUARANTINED
    return AdmissionStatus.ADMITTED


def admit_observation(
    request: ObservationAdmissionRequest,
) -> ObservationAdmissionResult:
    """Apply the fixed-order L2.0 admission policy without interpretation."""
    reason_codes = _reasons(request)
    status = _status(reason_codes)
    request_payload = _identity_safe(request.to_payload())
    input_hash = sha256_payload(request_payload)
    output_hash = sha256_payload(
        {
            "observation_id": request.observation.observation_id,
            "reason_codes": [reason.value for reason in reason_codes],
            "status": status.value,
        }
    )
    op_signature_hash = sha256_payload(
        {
            "admission_policy_version": request.admission_policy_version,
            "contract_version": CONTRACT_VERSION,
            "operation": OPERATION,
        }
    )
    return ObservationAdmissionResult(
        status=status,
        reason_codes=reason_codes,
        observation=request.observation,
        source=request.source,
        input_hash=input_hash,
        output_hash=output_hash,
        op_signature_hash=op_signature_hash,
        admission_policy_version=request.admission_policy_version,
    )
