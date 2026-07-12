# L5.4 Hypothesis Evaluation Trace

L5.4 defines the immutable trace that binds one exact L5.3 hypothesis-evaluation result to the ordered L5.2 relation-record identities used to produce it.

```text
HypothesisEvaluationResult
        + EvidenceHypothesisRelationRecord(s)
        ↓
HypothesisEvaluationTrace
```

## Contract surface

`HypothesisEvaluationTrace` contains only:

- `evaluation_result_hash`
- `ordered_relation_record_hashes`
- `trace_contract_version`
- `trace_hash`

The public constructor is disabled. Instances are created only through `build_hypothesis_evaluation_trace`.

## Deterministic identity

`trace_hash` is the canonical SHA-256 identity of:

- the exact L5.3 `result_hash`;
- the ordered L5.2 relation-record hashes;
- the L5.4 contract version.

The hash is excluded from its own preimage.

## Validation

The builder rejects:

- non-L5.3 result authority;
- non-L5.2 relation records;
- duplicate relation-record hashes;
- records absent from the supplied result;
- record order that differs from the evaluation result.

An empty trace remains valid when the L5.3 result contains no relation records.

## Explicit exclusions

L5.4 introduces no probability, confidence, weighting, ranking, Bayesian update, trajectory, drift, endpoint, location, search-area, causal, registry, persistence, clock, UUID, randomness, filesystem, network, or environment semantics.

## Completion condition

L5.4 is complete when an exact L5.3 result can be replayably bound to its ordered L5.2 record identities through a frozen, canonical, deterministic trace envelope.