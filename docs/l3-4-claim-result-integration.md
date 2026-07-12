# L3.4 Neutral Claim Integration

L3.4 integrates validated `NeutralDerivedClaim` objects into the deterministic `InterpretationResult` envelope.

## Authority path

```text
InterpretationRequest
    -> InterpretationResult
    -> tuple[NeutralDerivedClaim, ...]
```

This layer seals claims. It does not execute rules, infer facts, rank hypotheses, or reconstruct upstream authority.

## Accepted inputs

`build_interpretation_result(...)` accepts:

- one exact `InterpretationRequest`;
- one interpretation policy version;
- one allowlisted neutral status;
- ordered reason codes;
- an ordered tuple of exact `NeutralDerivedClaim` objects.

Empty claim tuples remain valid.

## Deterministic identity

Claim order is preserved and is part of the canonical result payload. Each full claim payload, including its content hash, contributes to `result_hash`.

The same request, policy version, status, reasons, and ordered claims produce the same result hash.

Changing claim order changes result identity.

## Lineage restriction

Every supporting evidence identifier used by a claim must belong to the request lineage:

- registry evidence identifier;
- evidence hash;
- validation hash.

Claims referring to any other identifier fail closed.

## Duplicate restriction

Two claims with the same `claim_hash` cannot appear in one result. Duplicate content-addressed claims are rejected rather than silently collapsed.

## Explicit exclusions

L3.4 contains no:

- interpretation rule execution;
- confidence, probability, likelihood, weighting, or ranking;
- Bayesian fusion;
- trajectory, drift, route, endpoint, coordinate, or location semantics;
- registry lookup or raw evidence retrieval;
- timestamps, UUIDs, randomness, filesystem, network, persistence, caching, or environment state.

## Completion condition

L3.4 is complete when an `InterpretationResult` can deterministically seal zero or more neutral claims, preserve their order and identities, and reject duplicate or out-of-lineage claims without receiving broader authority.