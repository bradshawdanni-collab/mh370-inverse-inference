"""Tests for the Issue #83 radar track input schema."""

from dataclasses import FrozenInstanceError, replace

import pytest

from mh370_inverse_inference.aircraft.radar import (
    RADAR_INPUT_CONTRACT_VERSION,
    RadarTrackPoint,
    RadarUncertainty,
    validate_radar_source,
)
from mh370_inverse_inference.provenance import (
    ArtifactAdmissionState,
    ArtifactKind,
    ArtifactProvenanceRecord,
    ArtifactReference,
    SourceReference,
    build_registry_snapshot,
)

SOURCE_REFERENCE = ArtifactReference(
    artifact_id="radar-source-example",
    version="v1",
    sha256="1" * 64,
)
SUPERSEDING_REFERENCE = ArtifactReference(
    artifact_id="radar-source-example",
    version="v2",
    sha256="2" * 64,
)
SOURCE_METADATA = SourceReference(
    source_id="radar-source-example",
    publisher="Example Radar Authority",
    title="Example radar source",
    reference_uri="https://example.invalid/radar-source",
    retrieved_at_utc="2026-07-29T00:00:00Z",
    licence_or_terms="Test fixture terms",
    content_hash=SOURCE_REFERENCE.sha256,
)


def _registry(state: ArtifactAdmissionState = ArtifactAdmissionState.PROPOSED):
    return build_registry_snapshot(
        (
            ArtifactProvenanceRecord(
                artifact=SOURCE_REFERENCE,
                kind=ArtifactKind.SOURCE,
                admission_state=state,
                source=SOURCE_METADATA,
                transformation_history=(),
                uncertainty_notes=(),
                limitations=(),
                superseded_by=(
                    SUPERSEDING_REFERENCE
                    if state is ArtifactAdmissionState.SUPERSEDED
                    else None
                ),
            ),
        )
    )


def _point() -> RadarTrackPoint:
    return RadarTrackPoint(
        timestamp_utc="2014-03-07T18:22:00Z",
        latitude_deg=6.0,
        longitude_deg=100.0,
        altitude_m=10668.0,
        groundspeed_mps=250.0,
        heading_deg=270.0,
        source_id=SOURCE_REFERENCE.artifact_id,
        source_version=SOURCE_REFERENCE.version,
        uncertainty=RadarUncertainty(
            position_m=1000.0,
            speed_mps=10.0,
            heading_deg=5.0,
        ),
    )


def test_valid_point_is_deterministic() -> None:
    point = _point()
    assert point.contract_version == RADAR_INPUT_CONTRACT_VERSION
    assert point.to_payload() == _point().to_payload()


def test_point_is_immutable() -> None:
    point = _point()
    with pytest.raises(FrozenInstanceError):
        point.heading_deg = 0.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,value",
    (
        ("latitude_deg", -90.1),
        ("latitude_deg", 90.1),
        ("longitude_deg", -180.1),
        ("longitude_deg", 180.1),
        ("heading_deg", -0.1),
        ("heading_deg", 360.0),
        ("groundspeed_mps", -1.0),
    ),
)
def test_invalid_numeric_fields_fail_closed(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        replace(_point(), **{field: value})


@pytest.mark.parametrize(
    "timestamp",
    (
        "2014-03-07T18:22:00+00:00",
        "2014-03-07 18:22:00Z",
        "not-a-time",
    ),
)
def test_invalid_timestamp_fails_closed(timestamp: str) -> None:
    with pytest.raises(ValueError):
        replace(_point(), timestamp_utc=timestamp)


def test_negative_uncertainty_fails_closed() -> None:
    with pytest.raises(ValueError):
        RadarUncertainty(position_m=-1.0, speed_mps=0.0, heading_deg=0.0)


def test_blank_source_identity_fails_closed() -> None:
    with pytest.raises(ValueError):
        replace(_point(), source_id="")
    with pytest.raises(ValueError):
        replace(_point(), source_version="")


def test_proposed_and_admitted_sources_are_allowed() -> None:
    validate_radar_source(_point(), _registry(ArtifactAdmissionState.PROPOSED))
    validate_radar_source(_point(), _registry(ArtifactAdmissionState.ADMITTED))


def test_missing_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="not present"):
        validate_radar_source(_point(), build_registry_snapshot(()))


@pytest.mark.parametrize(
    "state",
    (
        ArtifactAdmissionState.VERIFIED,
        ArtifactAdmissionState.REJECTED,
        ArtifactAdmissionState.SUPERSEDED,
    ),
)
def test_ungoverned_source_state_fails_closed(state: ArtifactAdmissionState) -> None:
    with pytest.raises(ValueError, match="PROPOSED or ADMITTED"):
        validate_radar_source(_point(), _registry(state))
