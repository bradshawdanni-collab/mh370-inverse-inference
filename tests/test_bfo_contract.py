"""Tests for the governed BFO source and calibration contract."""

from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.provenance import ArtifactAdmissionState
from mh370_inverse_inference.satcom.bfo_contract import BFOObservation


def _observation() -> BFOObservation:
    return BFOObservation(
        observation_id="BFO-2014-03-08T00:19:29Z",
        timestamp_utc="2014-03-08T00:19:29Z",
        bfo_hz=182.0,
        uncertainty_hz=7.0,
        source_artifact_id="published-bfo-table",
        source_artifact_version="v1",
        source_citation="Source table row for 00:19:29 UTC",
        calibration_source_id="bfo-calibration-register",
        calibration_source_version="v1",
        admission_state=ArtifactAdmissionState.PROPOSED,
    )


def test_payload_is_deterministic() -> None:
    first = _observation().to_payload()
    second = _observation().to_payload()
    assert first == second
    assert first["frequency_unit"] == "Hz"
    assert first["uncertainty_unit"] == "Hz"


def test_contract_is_immutable() -> None:
    observation = _observation()
    with pytest.raises(FrozenInstanceError):
        observation.bfo_hz = 183.0  # type: ignore[misc]


def test_negative_uncertainty_fails_closed() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        BFOObservation(
            observation_id="BFO-1",
            timestamp_utc="2014-03-08T00:19:29Z",
            bfo_hz=182.0,
            uncertainty_hz=-1.0,
            source_artifact_id="source",
            source_artifact_version="v1",
            source_citation="citation",
            calibration_source_id="calibration",
            calibration_source_version="v1",
            admission_state=ArtifactAdmissionState.PROPOSED,
        )


def test_non_canonical_timestamp_fails_closed() -> None:
    with pytest.raises(ValueError, match="canonical UTC"):
        BFOObservation(
            observation_id="BFO-1",
            timestamp_utc="2014-03-08 00:19:29",
            bfo_hz=182.0,
            uncertainty_hz=7.0,
            source_artifact_id="source",
            source_artifact_version="v1",
            source_citation="citation",
            calibration_source_id="calibration",
            calibration_source_version="v1",
            admission_state=ArtifactAdmissionState.PROPOSED,
        )


def test_wrong_frequency_unit_fails_closed() -> None:
    with pytest.raises(ValueError, match="must be Hz"):
        BFOObservation(
            observation_id="BFO-1",
            timestamp_utc="2014-03-08T00:19:29Z",
            bfo_hz=182.0,
            uncertainty_hz=7.0,
            source_artifact_id="source",
            source_artifact_version="v1",
            source_citation="citation",
            calibration_source_id="calibration",
            calibration_source_version="v1",
            admission_state=ArtifactAdmissionState.PROPOSED,
            frequency_unit="kHz",
        )
