# L3.2 deterministic interpretation result contract

L3.2 defines the neutral, immutable result envelope emitted from an L3.1 `InterpretationRequest`.

```text
InterpretationRequest
    -> InterpretationResult
```

The boundary is one-way. It does not expose registry authority, raw evidence, validation authority, or reconstruction paths.

## Result identity

`InterpretationResult.result_hash` is the canonical SHA-256 identity of:

- `input_hash`
- `interpretation_contract_version`
- `interpretation_policy_version`
- `status`
- ordered `reason_codes`
- empty `derived_claims`

The result hash is excluded from its own preimage. Canonical serialization uses the shared engine hashing implementation.

## Neutral statuses

- `ACCEPTED`
- `REJECTED`
- `INSUFFICIENT_EVIDENCE`

These statuses describe only the result envelope. They do not express a hypothesis, probability, trajectory, endpoint, or location conclusion.

## Derived claims

L3.2 fixes `derived_claims` to an empty immutable tuple. Domain claim semantics require a later, separately governed contract.

## Exclusions

L3.2 performs no registry lookup, raw-evidence retrieval, probability update, evidence weighting, ranking, Bayesian fusion, trajectory generation, drift modelling, endpoint interpretation, location claim, persistence, filesystem access, network access, clock access, UUID generation, or randomness.

## Completion invariant

An L3.1 request can be transformed into a deterministic, replayable and auditable result envelope without producing substantive MH370 inference.
