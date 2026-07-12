# L3.1 Interpretation Input Contract

## Purpose

L3.1 is a one-way deterministic adapter from the L3.0 accepted evidence boundary into the exact immutable request shape permitted for later interpretation layers.

```text
AcceptedEvidenceProjection
    -> InterpretationRequest
```

The layer canonicalizes and seals. It does not interpret, enrich, retrieve, rank, score, or infer.

## Governing invariant

No interpretation request may be constructed from raw evidence, registered evidence records, registered evidence projections, registry identifiers, dictionaries, or reconstructed payloads.

The only public construction path is:

```python
build_interpretation_request(accepted_projection)
```

## Deterministic identity

`InterpretationRequest.input_hash` is the SHA-256 identity of the canonical request payload. The payload uses stable field names and contains no timestamps, UUIDs, randomness, environment-derived values, or mutable metadata.

Identical accepted projections therefore produce identical requests and identical input hashes.

## Preserved lineage

L3.1 preserves only the lineage already admitted by L3.0:

- registry evidence identifier;
- evidence identifier;
- observation identifier;
- source identifier;
- evidence hash;
- validation hash;
- L3.0 consumption contract version.

It adds only the L3.1 interpretation contract version and the deterministic input hash.

## Explicit exclusions

L3.1 performs no:

- registry lookup or reverse reconstruction;
- raw evidence retrieval;
- persistence, caching, synchronization, or network access;
- timestamp or random identifier generation;
- likelihood, probability, score, weight, rank, or hypothesis calculation;
- trajectory, drift, endpoint, or location interpretation.

## Completion criterion

An interpretation engine can receive a deterministic, immutable, provenance-preserving request without receiving registry authority, raw-evidence authority, or interpretation logic.
