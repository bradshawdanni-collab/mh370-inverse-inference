# L4.3 Neutral Reasoning Trace Contract

## Purpose

L4.3 defines the immutable trace artifact that binds one exact L4.1 `ConstrainedReasoningResult` to an ordered sequence of L4.2 `RuleApplicationRecord` identities.

```text
ConstrainedReasoningResult
    -> RuleApplicationRecord(s)
    -> NeutralReasoningTrace
```

The trace records execution structure only. It does not introduce substantive MH370 conclusions or widen any prior result envelope.

## Contract surface

`NeutralReasoningTrace` contains only:

- `reasoning_result_hash`
- `ordered_rule_application_hashes`
- `trace_contract_version`
- `trace_hash`

The object is frozen, slotted, content-addressed, replayable, and unavailable through a public direct constructor.

## Deterministic identity

`trace_hash` is calculated with the repository `sha256_payload` helper from the canonical payload:

```text
reasoning_result_hash
ordered_rule_application_hashes
trace_contract_version
```

The trace hash is excluded from its own preimage. Rule-application order is identity-bearing.

## Lineage rules

Every supplied record must:

1. be an exact `RuleApplicationRecord`;
2. reference the exact supplied `ConstrainedReasoningResult.result_hash`;
3. have a unique `record_hash` within the trace.

An empty record sequence is valid and produces a deterministic empty trace.

## Boundary

L4.3 performs no registry lookup, evidence reconstruction, result reconstruction, persistence, caching, environment access, filesystem access, network access, time access, UUID generation, or randomness.

It contains no likelihoods, probabilities, confidence scores, rankings, Bayesian updates, hypothesis comparisons, trajectories, drift models, coordinates, routes, endpoints, locations, search-area recommendations, or causal conclusions.

`ConstrainedReasoningResult.reasoning_outputs` remains unchanged.

## Completion condition

L4.3 is complete when one exact reasoning result and its ordered neutral rule-application records can be sealed into a deterministic trace whose identity can be independently replayed and verified.
