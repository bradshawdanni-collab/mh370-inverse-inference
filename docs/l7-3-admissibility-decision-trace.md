# L7.3 — Admissibility Decision Trace

## Purpose

`AdmissibilityDecisionTrace` binds one exact L7.2 admissibility result to the ordered L7.1 decision records from which that result was formed.

```text
AdmissibilityDecisionResult
        + ordered AdmissibilityDecisionRecord(s)
        ↓
AdmissibilityDecisionTrace
```

## Contract surface

The trace preserves:

- the exact L7.2 admissibility result hash;
- the exact L7.0 admissibility request hash;
- the exact ordered L7.1 decision-record hashes;
- the L7.3 contract version;
- a deterministic SHA-256 trace identity.

## Validation

Construction rejects:

- values outside the exact contract types;
- decision records referencing another admissibility request;
- duplicate decision-record hashes;
- any record order different from the L7.2 result order.

The public constructor is disabled. Valid traces are produced only through `build_admissibility_decision_trace`.

## Canonical identity

`trace_hash` is derived through `sha256_payload` from the canonical payload containing:

```text
admissibility_request_hash
admissibility_result_hash
admissibility_trace_contract_version
ordered_record_hashes
```

## Boundary

This trace is structural and replayable. It introduces no probability, confidence, weighting, ranking, Bayesian semantics, trajectory, drift, endpoint, geographic conclusion, search-area authority, causality, clock, UUID, randomness, filesystem, network, persistence, registry, or execution authority.

## Governance

L7.3 is tracked by issue #160 under the active L7 umbrella issue #152. Ruff, Black, mypy, pytest, and DX.2 are required before merge.
