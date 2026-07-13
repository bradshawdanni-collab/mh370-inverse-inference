# L7.1 — Admissibility Decision Record

## Purpose

`AdmissibilityDecisionRecord` binds one comparative result admitted by an exact L7.0 request to an explicit, rule-versioned structural admissibility outcome.

```text
AdmissibilityDecisionRequest
        + admitted ComparativeAssessmentResult
        + explicit outcome
        + decision rule identity
        ↓
AdmissibilityDecisionRecord
```

## Contract surface

The immutable record preserves:

- the exact L7.0 request hash;
- the exact admitted L6 comparative result hash;
- one structural admissibility outcome;
- one decision-rule identifier;
- one decision-rule version;
- the L7.1 contract version;
- a deterministic SHA-256 record identity.

## Structural outcomes

The permitted outcome values are:

- `ADMISSIBLE`
- `INADMISSIBLE`
- `INDETERMINATE`
- `CONSTRAINT_VIOLATION`

These values are rule-bound structural dispositions. They do not encode probability, confidence, rank, geographic conclusions, operational priority, or execution authority.

## Membership rule

The supplied comparative result hash must occur in the exact ordered result-hash set preserved by the L7.0 request. A result outside that frozen request lineage is rejected.

## Deterministic identity

`record_hash` is the SHA-256 digest of canonical JSON over:

```text
admissibility_record_contract_version
admissibility_request_hash
comparative_result_hash
decision_rule_id
decision_rule_version
outcome
```

Changing any field changes the record identity.

## Boundary

L7.1 introduces no probability, confidence, weighting, ranking, Bayesian inference, trajectory, drift, endpoint, coordinate, location, search-area, causal, clock, UUID, randomness, filesystem, network, persistence, registry, or execution authority.

## Governance

This milestone is tracked by Issue #156 under the active L7 umbrella Issue #152. It must pass Ruff, Black, mypy, pytest, and DX.2 before merge.
