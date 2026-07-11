# L2.4 Evidence Registry Interface

L2.4 is a pure query layer over immutable snapshots of L2.3 registered evidence.

```text
immutable registry snapshot + request
                  ↓
        deterministic query result
```

The governing invariant is:

```text
same snapshot + same request = identical result
```

## Snapshot contract

`EvidenceRegistrySnapshot` contains only `RegisteredEvidenceRecord` values. Records must be ordered lexicographically by `registry_evidence_id`, IDs must be unique, and the supplied snapshot hash must equal the canonical hash of the ordered records and the L2.4 contract version.

## Operations

- `lookup(request)` returns `FOUND` or `NOT_FOUND` without mutating the snapshot.
- `contains(snapshot, registry_evidence_id)` is a pure convenience predicate.
- `list_by_observation(snapshot, observation_id)` returns a tuple ordered by `registry_evidence_id`.

An ordinary missing identity returns:

```text
status: NOT_FOUND
reason: EVIDENCE_NOT_REGISTERED
lookup: null
```

## Separation

Registration remains exclusively in L2.3. L2.4 does not create snapshots through mutation, persist data, manage lifecycle state, or interpret evidence.

Excluded concerns include databases, caches, timestamps, synchronization, Merkle proofs, signatures, likelihoods, Bayesian inference, trajectory ranking, drift, and endpoint semantics.
