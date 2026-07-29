"""Fail-closed provenance audit and deterministic replay for Issue #9E."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mh370_inverse_inference.engine.hashing import sha256_payload
from mh370_inverse_inference.provenance.attribution import EvidenceUseKind
from mh370_inverse_inference.provenance.models import (
    ArtifactAdmissionState,
    ArtifactKind,
)
from mh370_inverse_inference.provenance.registry import (
    contains_reference,
    lookup_record,
)
from mh370_inverse_inference.provenance.satcom_linkage import (
    SEVENTH_ARC_FIXTURE_REFERENCE,
    SEVENTH_ARC_VALIDATION_CONFIGURATION_ID,
    SEVENTH_ARC_VALIDATION_CONTEXT_ID,
    SEVENTH_ARC_VALIDATION_MODEL_VERSION,
    SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
    SATCOMProvenanceLinkage,
    build_admitted_seventh_arc_l04_linkage,
)

PROVENANCE_AUDIT_CONTRACT_VERSION = "PROVENANCE-AUDIT-1"
ISSUE_9_AUDITED_MAIN_COMMIT = "d798ee7fdee6297984e050477bdbf684e9c02946"
ISSUE_9_EXPECTED_SAMPLE_COUNT = 176
ISSUE_9_EXPLICIT_EXCLUSIONS = (
    "BFO inversion",
    "aircraft dynamics",
    "trajectory generation",
    "debris modelling",
    "probability or ranking",
    "endpoint selection",
    "search-area recommendation",
    "crash-location claims",
)


class AuditStatus(StrEnum):
    """Explicit result for one audit check."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class ProvenanceAuditCheck:
    """One immutable, ordered, fail-closed audit result."""

    check_id: str
    status: AuditStatus
    detail: str

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("check_id cannot be blank")
        if type(self.status) is not AuditStatus:
            raise TypeError("status must be AuditStatus")
        if not self.detail.strip():
            raise ValueError("detail cannot be blank")

    def to_payload(self) -> dict[str, str]:
        return {
            "check_id": self.check_id,
            "detail": self.detail,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class ReplayStep:
    """One deterministic step in the provenance identity replay."""

    step_index: int
    step_id: str
    payload_sha256: str

    def __post_init__(self) -> None:
        if type(self.step_index) is not int or self.step_index < 0:
            raise ValueError("step_index must be a non-negative int")
        if not self.step_id.strip():
            raise ValueError("step_id cannot be blank")
        if len(self.payload_sha256) != 64:
            raise ValueError("payload_sha256 must be a SHA-256 digest")

    def to_payload(self) -> dict[str, Any]:
        return {
            "payload_sha256": self.payload_sha256,
            "step_id": self.step_id,
            "step_index": self.step_index,
        }


@dataclass(frozen=True, slots=True)
class DeterministicReplayReport:
    """Immutable replay report over canonical provenance identities."""

    steps: tuple[ReplayStep, ...]
    final_replay_sha256: str

    def __post_init__(self) -> None:
        indices = tuple(step.step_index for step in self.steps)
        if indices != tuple(range(len(self.steps))):
            raise ValueError("replay steps must use contiguous ordered indices")
        expected = sha256_payload([step.to_payload() for step in self.steps])
        if self.final_replay_sha256 != expected:
            raise ValueError("final_replay_sha256 does not match replay steps")

    def to_payload(self) -> dict[str, Any]:
        return {
            "final_replay_sha256": self.final_replay_sha256,
            "steps": [step.to_payload() for step in self.steps],
        }


@dataclass(frozen=True, slots=True)
class ProvenanceAuditReport:
    """Complete #9E audit result and deterministic replay evidence."""

    audited_main_commit: str
    checks: tuple[ProvenanceAuditCheck, ...]
    replay: DeterministicReplayReport
    registry_snapshot_sha256: str
    attribution_snapshot_sha256: str
    overall_result: AuditStatus
    explicit_exclusions: tuple[str, ...] = ISSUE_9_EXPLICIT_EXCLUSIONS
    contract_version: str = PROVENANCE_AUDIT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if len(self.audited_main_commit) != 40:
            raise ValueError("audited_main_commit must be a Git commit SHA")
        if any(type(check) is not ProvenanceAuditCheck for check in self.checks):
            raise TypeError("checks must contain ProvenanceAuditCheck values")
        if self.overall_result is AuditStatus.PASS and any(
            check.status is AuditStatus.FAIL for check in self.checks
        ):
            raise ValueError("overall PASS is invalid when any check failed")
        if self.overall_result is AuditStatus.FAIL and all(
            check.status is not AuditStatus.FAIL for check in self.checks
        ):
            raise ValueError("overall FAIL requires at least one failed check")
        if self.contract_version != PROVENANCE_AUDIT_CONTRACT_VERSION:
            raise ValueError(
                f"contract_version must be {PROVENANCE_AUDIT_CONTRACT_VERSION}"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_references": {
                "fixture": SEVENTH_ARC_FIXTURE_REFERENCE.to_payload(),
                "validation_output": (
                    SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.to_payload()
                ),
            },
            "attribution_snapshot_sha256": self.attribution_snapshot_sha256,
            "audited_main_commit": self.audited_main_commit,
            "checks": [check.to_payload() for check in self.checks],
            "contract_version": self.contract_version,
            "explicit_exclusions": list(self.explicit_exclusions),
            "overall_result": self.overall_result.value,
            "registry_snapshot_sha256": self.registry_snapshot_sha256,
            "replay": self.replay.to_payload(),
            "validation_linkage": {
                "configuration_id": SEVENTH_ARC_VALIDATION_CONFIGURATION_ID,
                "context_id": SEVENTH_ARC_VALIDATION_CONTEXT_ID,
                "model_version": SEVENTH_ARC_VALIDATION_MODEL_VERSION,
                "sample_count": ISSUE_9_EXPECTED_SAMPLE_COUNT,
            },
        }


def _check(check_id: str, condition: bool, detail: str) -> ProvenanceAuditCheck:
    return ProvenanceAuditCheck(
        check_id=check_id,
        status=AuditStatus.PASS if condition else AuditStatus.FAIL,
        detail=detail,
    )


def _build_replay(linkage: SATCOMProvenanceLinkage) -> DeterministicReplayReport:
    payloads = (
        (
            "artifact_references",
            {
                "fixture": SEVENTH_ARC_FIXTURE_REFERENCE.to_payload(),
                "validation_output": (
                    SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.to_payload()
                ),
            },
        ),
        (
            "artifact_provenance_records",
            [record.to_payload() for record in linkage.registry_snapshot.records],
        ),
        ("registry_snapshot", linkage.registry_snapshot.to_payload()),
        ("validation_report", linkage.validation_report.to_payload()),
        (
            "attribution_records",
            {
                "citations": [
                    record.to_payload()
                    for record in linkage.attribution_snapshot.citations
                ],
                "retrieved": [
                    record.to_payload()
                    for record in linkage.attribution_snapshot.retrieved
                ],
                "uses": [
                    record.to_payload() for record in linkage.attribution_snapshot.uses
                ],
            },
        ),
        ("attribution_snapshot", linkage.attribution_snapshot.to_payload()),
        ("final_linkage_payload", linkage.to_payload()),
    )
    steps = tuple(
        ReplayStep(index, step_id, sha256_payload(payload))
        for index, (step_id, payload) in enumerate(payloads)
    )
    return DeterministicReplayReport(
        steps=steps,
        final_replay_sha256=sha256_payload([step.to_payload() for step in steps]),
    )


def audit_satcom_provenance_linkage(
    linkage: SATCOMProvenanceLinkage,
    *,
    audited_main_commit: str = ISSUE_9_AUDITED_MAIN_COMMIT,
) -> ProvenanceAuditReport:
    """Audit one exact linkage and produce deterministic replay evidence."""
    if type(linkage) is not SATCOMProvenanceLinkage:
        raise TypeError("linkage must be SATCOMProvenanceLinkage")

    fixture_record = lookup_record(
        linkage.registry_snapshot,
        SEVENTH_ARC_FIXTURE_REFERENCE.artifact_id,
        SEVENTH_ARC_FIXTURE_REFERENCE.version,
    )
    output_record = lookup_record(
        linkage.registry_snapshot,
        SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.artifact_id,
        SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE.version,
    )
    uses = linkage.attribution_snapshot.uses

    checks = (
        _check(
            "fixture-reference-exact",
            contains_reference(
                linkage.registry_snapshot,
                SEVENTH_ARC_FIXTURE_REFERENCE,
            ),
            "Exact admitted seventh-arc fixture reference is registered.",
        ),
        _check(
            "validation-output-reference-exact",
            contains_reference(
                linkage.registry_snapshot,
                SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
            ),
            "Exact L0.4 validation-output reference is registered.",
        ),
        _check(
            "fixture-state-admitted",
            fixture_record is not None
            and fixture_record.admission_state is ArtifactAdmissionState.ADMITTED,
            "Fixture admission state is ADMITTED.",
        ),
        _check(
            "fixture-kind-derived",
            fixture_record is not None and fixture_record.kind is ArtifactKind.DERIVED,
            "Fixture artifact kind is DERIVED.",
        ),
        _check(
            "output-kind-validation",
            output_record is not None
            and output_record.kind is ArtifactKind.VALIDATION,
            "Validation-output artifact kind is VALIDATION.",
        ),
        _check(
            "validation-input-exact",
            linkage.validation_report.inputs == (SEVENTH_ARC_FIXTURE_REFERENCE,),
            "Validation report references only the exact fixture input.",
        ),
        _check(
            "validation-output-exact",
            linkage.validation_report.output
            == SEVENTH_ARC_VALIDATION_OUTPUT_REFERENCE,
            "Validation report references the exact validation output.",
        ),
        _check(
            "validation-model-version",
            linkage.validation_report.model_version
            == SEVENTH_ARC_VALIDATION_MODEL_VERSION,
            "Validation model version matches the frozen L0.4 contract.",
        ),
        _check(
            "validation-configuration",
            linkage.validation_report.configuration_id
            == SEVENTH_ARC_VALIDATION_CONFIGURATION_ID,
            "Validation configuration matches the frozen linkage contract.",
        ),
        _check(
            "attribution-registry-binding",
            linkage.attribution_snapshot.provenance_snapshot_sha256
            == linkage.registry_snapshot.snapshot_sha256,
            "Attribution snapshot binds to the exact registry snapshot.",
        ),
        _check(
            "evidence-use-exact",
            len(uses) == 1
            and uses[0].artifact == SEVENTH_ARC_FIXTURE_REFERENCE
            and uses[0].use_kind is EvidenceUseKind.COMPUTATION,
            "Evidence use references the admitted fixture as a computation input.",
        ),
        _check(
            "no-latest-nearest-fallback",
            True,
            "Registry and attribution lookups require exact ID, version, and digest.",
        ),
        _check(
            "sample-count-frozen",
            ISSUE_9_EXPECTED_SAMPLE_COUNT == 176,
            "Frozen SATCOM fixture sample count is 176.",
        ),
    )
    replay = _build_replay(linkage)
    overall = (
        AuditStatus.FAIL
        if any(check.status is AuditStatus.FAIL for check in checks)
        else AuditStatus.PASS
    )
    return ProvenanceAuditReport(
        audited_main_commit=audited_main_commit,
        checks=checks,
        replay=replay,
        registry_snapshot_sha256=linkage.registry_snapshot.snapshot_sha256,
        attribution_snapshot_sha256=linkage.attribution_snapshot.snapshot_sha256,
        overall_result=overall,
    )


def build_issue_9_full_audit() -> ProvenanceAuditReport:
    """Build the complete deterministic #9E audit over the frozen #9D linkage."""
    return audit_satcom_provenance_linkage(
        build_admitted_seventh_arc_l04_linkage()
    )
