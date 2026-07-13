# L7 — Admissibility Decision Synthesis

## Status

L6 is complete, frozen, and published as `l6-v1.0.0`.

L7 opens the deterministic admissibility-decision-synthesis layer over the frozen comparative-assessment surface.

## Governing flow

```text
ComparativeAssessmentResult(s)
        +
ComparativeAssessmentTrace(s)
        ↓
AdmissibilityDecisionRequest
        ↓
AdmissibilityDecisionRecord
        ↓
AdmissibilityDecisionResult
        ↓
AdmissibilityDecisionTrace
        ↓
L7 release freeze
```

## Planned sequence

1. L7.0 — `AdmissibilityDecisionRequest`
2. L7.1 — `AdmissibilityDecisionRecord`
3. L7.2 — `AdmissibilityDecisionResult`
4. L7.3 — `AdmissibilityDecisionTrace`
5. L7.4 — L7 release freeze

## Structural purpose

L7 converts exact frozen L6 comparative lineage into explicit admissibility decisions under identified and versioned rules.

The layer does not determine physical truth, geographic position, search priority, or operational action. It records only whether supplied comparative material is admissible under the declared decision policy.

## Decision surface

The initial neutral outcome surface is:

- `ADMISSIBLE`
- `INADMISSIBLE`
- `INDETERMINATE`
- `CONSTRAINT_VIOLATION`

Each outcome must be accompanied by machine-readable reason codes and exact rule lineage.

## L7.0 entry contract

`AdmissibilityDecisionRequest` should bind:

- an exact ordered tuple of frozen L6 result hashes;
- an exact ordered tuple of matching L6 trace hashes;
- one-to-one result/trace lineage;
- an explicit admissibility-policy version;
- the L7.0 contract version;
- a deterministic canonical `request_hash`.

The request must reject:

- fewer than one admitted comparative result;
- mismatched result and trace counts;
- result/trace lineage mismatches;
- duplicate result hashes;
- duplicate trace hashes;
- blank policy versions;
- malformed SHA-256 identities.

## Deterministic requirements

Every L7 contract must use:

- frozen and slotted value objects;
- disabled public constructors;
- canonical JSON payloads;
- SHA-256 content identities;
- exact ordered lineage preservation;
- explicit contract, policy, and rule versions;
- replayable payloads;
- strict type, membership, duplicate, and order validation.

## Boundary

L7 introduces no:

- probability or confidence;
- weighting or ranking;
- Bayesian semantics;
- trajectory, drift, endpoint, coordinate, location, or search-area claims;
- causal authority;
- clock, UUID, or randomness;
- filesystem, network, persistence, registry, or execution authority.

## Validation gate

Each milestone remains unmergeable until all required checks pass:

```text
ruff check .
black --check .
mypy src
pytest
DX.2 Compliance Check
```

## Active milestone

Issue #152 governs the phase. The first implementation step is L7.0 — `AdmissibilityDecisionRequest`.
