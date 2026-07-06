# L10.5 Deterministic Reference Engine

The L10.5 reference engine is the canonical single-threaded execution path for the engine boundary introduced in L10.1. It exists to provide a small, replayable baseline before any optimized or multi-scenario engine behavior is added.

## Canonical input

The reference path is pinned to one frozen Bayesian fixture:

```text
tests/fixtures/bayesian/case_001.input.json
```

This fixture supplies the hypotheses, SATCOM observations, simulated BTO/BFO values, trajectory residuals, negative-search detection probabilities, and fusion parameters used by the L9 evidence pipeline.

## Execution path

The reference engine performs exactly one deterministic pipeline:

1. adapter normalization / fixture loading
2. likelihood evaluation through the existing evidence orchestrator
3. Bayesian fusion through the existing L9 fusion function
4. constraint application placeholder metrics
5. posterior normalization response assembly

The reference engine does not introduce new Bayesian math, optimization, caching, retry logic, stochastic execution, or alternate fixture routing.

## Trace substrate

The reference response is assembled over the L10 trace substrate:

- L10.2 canonical hashing utilities
- L10.3 immutable trace metric records
- L10.4 execution trace builder
- L10.1 engine response contract

Every public trace step includes input, output, and operation-signature hashes. The response also emits a replay hash over the ordered execution evidence.

## Release fixture policy

The release fixture freezes the normalized public response shape in:

```text
tests/fixtures/engine/reference_case_001.expected.json
```

Cryptographic hash values are normalized to the string `<sha256>` inside the expected JSON fixture. The integration test validates the actual hashes separately as lowercase 64-character SHA-256 hex strings.

This split keeps the fixture readable while still enforcing hash presence and format.

## Snapshot update policy

Do not update the expected fixture automatically. Treat any fixture change as a contract change requiring review.

Expected fixture changes are valid only when one of these changes intentionally occurs:

- the reference engine public response shape changes;
- the canonical stage order changes;
- the frozen posterior probabilities change due to an approved L9 fusion update;
- the L10 engine contract changes.

Incidental fields should be normalized rather than snapshotted.
