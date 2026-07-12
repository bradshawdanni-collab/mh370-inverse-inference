# L3.3 Neutral Derived Claim Contract

## Purpose

L3.3 defines the first schema-controlled derived claim emitted by the interpretation layer without introducing substantive MH370 inference.

```text
InterpretationRequest
    -> InterpretationResult
    -> NeutralDerivedClaim
```

The claim contract is independent of the L3.2 result envelope. `InterpretationResult.derived_claims` remains unchanged in this milestone.

## Contract surface

A `NeutralDerivedClaim` contains only:

- `claim_id`
- `claim_type`
- `statement`
- `supporting_evidence_ids`
- `interpretation_rule_id`
- `interpretation_rule_version`
- `claim_status`
- `claim_hash`
- `claim_contract_version`

`claim_id` is exactly equal to `claim_hash`. No UUID, clock, sequence, database, or registry state participates in identity.

## Canonical identity

The claim hash is computed with the repository `sha256_payload` helper over:

- `claim_contract_version`
- `claim_status`
- `claim_type`
- `interpretation_rule_id`
- `interpretation_rule_version`
- `statement`
- ordered `supporting_evidence_ids`

The hash and ID are excluded from their own preimage.

## Allowed claim types

L3.3 permits only neutral structural claims:

- `SOURCE_PRESENT`
- `OBSERVATION_LINKED`
- `VALIDATION_PASSED`
- `EVIDENCE_CONSUMED`
- `RULE_APPLIED`

## Lineage boundary

Claims are built only through `build_neutral_derived_claim(...)`. Every supporting evidence ID must be contained in the explicitly supplied immutable permitted-lineage set.

The builder performs no registry lookup, raw-evidence reconstruction, persistence, network access, or environmental access.

## Exclusions

L3.3 contains no:

- confidence, likelihood, or probability;
- evidence weighting or ranking;
- Bayesian fusion;
- trajectory or drift modelling;
- coordinates, endpoints, routes, or location claims;
- causal conclusions;
- clocks, UUIDs, randomness, filesystem, persistence, or network access.

## Completion gate

L3.3 is complete when neutral claims are deterministic, frozen, content-addressed, lineage constrained, independently testable, and accepted by Ruff, Black, mypy, pytest, and DX.2.
