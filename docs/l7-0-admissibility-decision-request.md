# L7.0 — Admissibility Decision Request

## Purpose

`AdmissibilityDecisionRequest` is the deterministic entry contract for L7 admissibility decision synthesis.

It binds an exact ordered set of frozen L6 comparative results and matching traces into one content-addressed request.

```text
ComparativeAssessmentResult(s)
        +
ComparativeAssessmentTrace(s)
        ↓
AdmissibilityDecisionRequest
```

## Contract surface

The request preserves:

- ordered comparative result hashes;
- ordered comparative trace hashes;
- an explicit admissibility-policy version;
- the L7.0 contract version;
- a canonical SHA-256 request identity.

## Validation

The builder rejects:

- an empty result set;
- unequal result and trace counts;
- duplicate result hashes;
- duplicate trace hashes;
- traces that do not reference their paired result;
- traces that do not preserve the paired comparative-request lineage;
- blank admissibility-policy versions;
- incorrect input object types.

Order is authoritative. Reordering valid result/trace pairs changes the request identity.

## Neutral boundary

L7.0 admits lineage into synthesis but does not itself decide admissibility.

It introduces no:

- probability or confidence;
- weighting or ranking;
- Bayesian semantics;
- trajectory, drift, endpoint, coordinate, location, or search-area conclusion;
- causal conclusion;
- clock, UUID, or randomness;
- filesystem, network, persistence, database, or registry authority;
- execution authority.

## Lifecycle

Issue #154 implements this milestone under the active L7 umbrella, Issue #152.

The contract remains provisional until Ruff, Black, mypy, pytest, and DX.2 pass and the pull request is merged.
