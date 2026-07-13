# L7.2 — Admissibility Decision Result

## Purpose

`AdmissibilityDecisionResult` seals the ordered L7.1 decision records produced under one exact L7.0 admissibility request into a deterministic aggregate result.

```text
AdmissibilityDecisionRequest
        + ordered AdmissibilityDecisionRecord(s)
        + aggregate structural status and reasons
        ↓
AdmissibilityDecisionResult
```

## Contract identity

- Contract version: `L7.2`
- Identity field: `result_hash`
- Hash function: canonical JSON through `sha256_payload`
- Object shape: frozen, slotted, public constructor disabled

## Canonical fields

- `admissibility_request_hash`
- `ordered_record_hashes`
- `status`
- `reason_codes`
- `admissibility_result_contract_version`

`result_hash` is derived from those exact fields.

## Aggregate statuses

- `COMPLETED`
- `REJECTED`
- `INSUFFICIENT_BASIS`
- `CONSTRAINT_VIOLATION`

## Reason codes

- `OK`
- `POLICY_REJECTED`
- `INSUFFICIENT_BASIS`
- `CONSTRAINT_VIOLATION`

Statuses and reason codes are structural machine-readable dispositions. They do not express probability, confidence, ranking, geographic inference, operational priority, or execution authority.

## Validation

The builder rejects:

- values that are not exact L7.0 request or L7.1 record types;
- records that do not reference the supplied request;
- duplicate record hashes;
- invalid status types;
- empty reason-code tuples;
- invalid reason-code types;
- non-canonical hashes or contract versions.

Record order is preserved exactly and participates in the result identity.

## Boundary

This contract introduces no probability, confidence, weighting, ranking, Bayesian, trajectory, drift, endpoint, coordinate, location, search-area, causal, clock, UUID, randomness, filesystem, network, persistence, registry, or execution authority.

## Governance

L7.2 is tracked by milestone issue #158 under the active L7 umbrella issue #152. Ruff, Black, mypy, pytest, and DX.2 must pass before merge.
