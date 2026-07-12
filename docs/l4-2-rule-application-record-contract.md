# L4.2 deterministic rule application record contract

L4.2 defines a neutral, immutable record of one rule application over an exact L4.1 reasoning result.

```text
ConstrainedReasoningResult
    -> RuleApplicationRecord
```

## Boundary

A record preserves the exact upstream reasoning-result hash, rule identity and version, ordered input-claim hashes, neutral outcome, ordered reason codes, contract version, and deterministic record hash.

Construction is permitted only through `build_rule_application_record`. The public dataclass constructor is disabled.

## Canonical identity

`record_hash` is produced with the repository `sha256_payload` helper over:

- `reasoning_result_hash`
- `rule_application_contract_version`
- `rule_id`
- `rule_version`
- ordered `input_claim_hashes`
- `outcome`
- ordered `reason_codes`

The record hash is not included in its own preimage.

## Lineage constraint

Every input claim hash must occur in the immutable `permitted_claim_hashes` set supplied to the factory. The contract performs no lookup or authority recovery.

## Neutral outcomes

- `APPLIED`
- `NOT_APPLIED`
- `INSUFFICIENT_BASIS`
- `CONSTRAINT_BLOCKED`

These outcomes record rule execution state only. They do not express a probability, ranking, route, location, endpoint, search-area recommendation, or causal conclusion.

## Deferred integration

L4.2 does not modify `ConstrainedReasoningResult.reasoning_outputs`. Integration of rule records into a neutral reasoning trace is deferred to L4.3.

## Exclusions

The module contains no clocks, UUIDs, randomness, persistence, filesystem, environment, network, registry reconstruction, raw-evidence reconstruction, Bayesian processing, weighting, ranking, trajectory, drift, location, endpoint, search-area, or causal semantics.
