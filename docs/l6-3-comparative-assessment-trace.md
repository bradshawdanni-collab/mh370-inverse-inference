# L6.3 Comparative Assessment Trace

## Purpose

`ComparativeAssessmentTrace` closes the deterministic comparative-assessment chain by binding one exact L6.2 result to the exact ordered L6.1 records that produced it.

```text
ComparativeAssessmentResult
        + ordered ComparativeAssessmentRecord(s)
        ↓
ComparativeAssessmentTrace
```

## Contract

The trace preserves:

- the exact comparative result hash;
- the exact comparative request hash inherited by that result;
- the exact ordered record hashes;
- the L6.3 contract version;
- a deterministic canonical trace hash.

Construction rejects records from another request, duplicate record hashes, and any order that differs from the result's ordered record lineage.

## Boundary

The trace is structural and replay-oriented only. It adds no probability, confidence, weighting, ranking, Bayesian, trajectory, drift, endpoint, location, search-area, causal, temporal, registry, persistence, filesystem, network, UUID, or randomness authority.

## Determinism

The trace is a frozen, slotted value object with a disabled public constructor. `trace_hash` is derived only from the canonical payload through `sha256_payload`.
