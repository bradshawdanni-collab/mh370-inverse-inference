# L2.2 Evidence Validation and Conformance

L2.2 is the deterministic trust gate for assembled L2.1 evidence packages.

```text
L2.0 admits observations.
L2.1 assembles evidence.
L2.2 validates the assembled package.
Later layers interpret it.
```

## Responsibilities

L2.2 verifies:

- assembly completion;
- evidence-record presence;
- contract-version identity;
- frozen evidence hash identity;
- observation and source identity continuity;
- provenance index order;
- provenance hash continuity;
- deterministic validation hashes;
- compatibility with the shared trace contract.

## Fail-closed behavior

Any conformance failure returns `REJECTED` with stable machine-readable reason codes. The validator does not repair, reinterpret, or silently normalize malformed packages.

Reason-code ordering is deterministic and follows the validation sequence:

1. assembly state;
2. evidence-record presence;
3. contract version;
4. frozen evidence hash;
5. observation identity;
6. source identity;
7. provenance structure and continuity.

## Replay identity

The caller supplies the expected canonical SHA-256 hash for the assembled `EvidenceRecord`. L2.2 recomputes the hash from the production payload and rejects any mismatch. This verifies replay identity without reimplementing L2.1 assembly semantics.

## Trace mapping

`validation_result_to_trace(...)` maps the immutable result into `TraceMetricRecord` using the shared L10 trace hash composition. A valid package maps to `TraceStatus.OK`; rejection maps to `TraceStatus.FAILED` with the first stable reason code as `failure_kind`.

## Explicit exclusions

L2.2 does not construct likelihoods, assign Bayesian weights, calculate posteriors, rank trajectories, model drift, interpret endpoints, or make crash-location claims.
