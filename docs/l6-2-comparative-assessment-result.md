# L6.2 Comparative Assessment Result

## Purpose

`ComparativeAssessmentResult` is the immutable aggregate output for one exact L6.0 comparative request and its ordered L6.1 comparison records.

```text
ComparativeAssessmentRequest
        + ordered ComparativeAssessmentRecord(s)
        + aggregate status and reasons
        ↓
ComparativeAssessmentResult
```

## Contract surface

The result preserves:

- the exact comparative request hash;
- the exact ordered comparison-record hashes;
- an explicit aggregate status;
- ordered machine-readable reason codes;
- the L6.2 contract version;
- a deterministic result hash derived from the canonical payload.

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

## Validation

The public builder rejects:

- values that are not exact L6.0 requests or L6.1 records;
- records that reference another comparative request;
- duplicate record hashes;
- invalid aggregate-status values;
- empty or invalid reason-code tuples.

The value object is frozen, slotted, content addressed, and unavailable through a public constructor.

## Neutral boundary

The contract aggregates structural comparison records only. It does not assign truth, preference, rank, probability, confidence, evidential weight, Bayesian posterior, physical plausibility, trajectory, drift, endpoint, coordinate, location, or search area.

It also has no clock, UUID, randomness, filesystem, network, persistence, database, or registry authority.

## Determinism

The result hash is:

```text
sha256_payload(result.canonical_payload())
```

Rebuilding the same result from the same request, ordered records, status, and reason codes produces the same identity.
