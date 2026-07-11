# L3.0 Registered Evidence Consumption Contract

L3.0 is a one-way projection gate between registered evidence authority and later interpretation layers.

```text
L2.4 registry snapshot
        |
        v
RegisteredEvidenceRecord
        |
        v
RegisteredEvidenceProjection
        |
        v
L3.0 consumption gate
        |
        v
AcceptedEvidenceProjection
```

## Governing invariant

No downstream interpretation input may be constructed from raw evidence, validation results, registry lookups, dictionaries, or registry identifiers alone.

## Authority rule

`RegisteredEvidenceProjection` has no public field constructor. It is created through:

```python
RegisteredEvidenceProjection.from_registered_record(record)
```

The constructor requires an immutable L2.3 `RegisteredEvidenceRecord` and copies its registry, evidence, observation, source, evidence-hash, validation-hash, and registration-contract identities exactly.

L3.0 may reduce registered authority into a projection. It does not expand a projection back into a registry record.

## Consumption gate

`consume_registered_evidence(...)` verifies:

- the requested L3.0 contract version;
- the registered projection identity shape;
- required lineage identifiers;
- the expected registry evidence identity.

An accepted request emits `AcceptedEvidenceProjection`. A rejected request emits no accepted projection and uses stable reason codes.

## Determinism

For a fixed request:

```text
same registered projection + same expected identity + same policy = same result
```

Input, output, and operation identities use canonical SHA-256 hashing. No wall-clock time, registry query, ambient state, or mutable storage participates in the result.

## Explicit exclusions

L3.0 performs no registry lookup, evidence registration, upstream replay, state reconstruction, raw-evidence retrieval, likelihood construction, weighting, ranking, Bayesian inference, trajectory analysis, drift analysis, endpoint interpretation, persistence, caching, or synchronization.
