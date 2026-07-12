# L3.6 Shared Trace and Replay Fixture

L3.6 completes the executable L3 interpretation path by mapping neutral interpretation outcomes into the repository-wide immutable trace contract.

## Governing path

```text
InterpretationRequest
    -> NeutralRuleExecution
    -> InterpretationResult
    -> TraceMetricRecord
```

## Fixed stage identity

```text
L3.6-neutral-interpretation-execution
```

The trace preserves:

- request `input_hash`;
- result `result_hash` as `output_hash`;
- rule `op_signature_hash`;
- ordered neutral-claim hashes;
- rule ID and version;
- interpretation contract and policy versions;
- status and reason codes.

## Outcome mapping

| Interpretation outcome | Shared trace status |
|---|---|
| Accepted | `ok` |
| Insufficient evidence/support | `partial` |
| Rejected/withheld | `failed` |

A rejected result records its first stable reason code as `failure_kind`. An insufficient-support result remains partial and does not claim execution failure.

## Replay fixture

`tests/fixtures/interpretation/l3_6_replay_case_001.json` freezes the canonical request inputs, neutral rule, policy version, stage index, and stage identity used by the deterministic replay test.

The replay test proves that identical fixture input produces identical:

- execution records;
- interpretation results;
- claim hashes;
- operation signatures;
- trace records;
- trace hashes.

## Tamper detection

`verify_interpretation_trace(...)` recomputes the shared step hash from the input, output, and operation-signature hashes. Any altered trace hash fails verification.

## Exclusions

L3.6 does not introduce probability, confidence, likelihood, weighting, ranking, Bayesian fusion, trajectory, drift, coordinates, routes, endpoints, locations, causal inference, registry access, raw-evidence retrieval, clocks, UUIDs, randomness, persistence, caching, networking, or environment-derived state.
