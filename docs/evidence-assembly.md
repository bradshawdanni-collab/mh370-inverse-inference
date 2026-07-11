# L2.1 Observation Evidence Assembly

## Purpose

L2.1 is a deterministic packaging layer. It accepts only observation admission results whose status is `ADMITTED`, preserves L2.0 identities directly, validates provenance ordering, and emits immutable evidence records with canonical identity and shared trace compatibility.

It does not interpret evidence.

## Governing separation

```text
L2.0 decides whether evidence may enter.
L2.1 packages admitted evidence.
Later inference determines what the evidence means.
```

## Accepted input

The assembly boundary accepts only `ObservationAdmissionResult` values with:

```text
status = ADMITTED
```

`REJECTED` and `QUARANTINED` admission results are rejected deterministically and cannot produce an `EvidenceRecord`.

## Identity preservation

L2.1 preserves L2.0 identity fields without recomputation:

```text
EvidenceRecord.observation_id
    = admission_result.observation.observation_id

EvidenceRecord.observation_type
    = admission_result.observation.observation_type

EvidenceRecord.observation_hash
    = admission_result.output_hash

EvidenceRecord.source_id
    = admission_result.observation.source_id

EvidenceRecord.source_hash
    = admission_result.source.content_hash
```

The evidence layer does not recompute observation values, units, uncertainty, admission status, source identity, or provenance status.

## Immutable contracts

The L2.1 contract consists of:

- `EvidenceProvenanceLink`
- `EvidenceRecord`
- `EvidenceAssemblyRequest`
- `EvidenceAssemblyResult`
- `EvidenceAssemblyStatus`
- `EvidenceAssemblyReason`

All value objects are immutable and canonically serializable.

## Provenance ordering

Provenance chains are explicit, ordered, and immutable.

Each link carries an exact `link_index`. Assembly accepts only zero-based contiguous ordering:

```text
0, 1, 2, ...
```

The layer does not reorder links and does not synthesize missing links from assumptions.

## Deterministic assembly

The core operation is:

```text
assemble_evidence(request) -> EvidenceAssemblyResult
```

The implementation has:

- no hidden global state;
- no network access;
- no randomness;
- no wall-clock dependency;
- fixed validation order;
- stable reason-code ordering;
- canonical replay identity;
- no mutation of source inputs.

## Canonical identity

L2.1 generates exact canonical hashes for:

- assembly input identity;
- assembly output identity;
- operation signature identity.

Scientific tolerances do not apply to these hashes. They are exact identity artifacts.

## Trace integration

Evidence assembly maps into the shared L10 trace contract only through:

```python
TraceMetricRecord.from_parts(...)
```

The mapping preserves:

- `input_hash`;
- `output_hash`;
- `op_signature_hash`;
- explicit `stage_index`;
- `record_count = 1` for assembled results;
- `record_count = 0` for rejected results;
- `OK` or `FAILED` status;
- primary failure reason;
- canonical evidence metadata.

The Bayesian-only fields remain unset:

```text
hypothesis_count = None
normalization_error = None
pre_normalization_mass = None
```

`duration_ms` is optional execution metadata and does not participate in identity.

## Frozen fixtures and replay

The contract-freeze gate covers:

- BTO assembled evidence;
- BFO assembled evidence;
- rejected source;
- quarantined source;
- invalid provenance ordering.

The frozen manifest records exact:

- `input_hash`;
- `output_hash`;
- assembly status;
- `trace_hash`.

The replay harness reconstructs every case and verifies:

- exact manifest equality;
- canonical trace metadata;
- identical replay output;
- duration-independent trace identity;
- unchanged request, admission, and source objects;
- unset Bayesian-only trace fields.

## Explicit exclusions

L2.1 does not contain:

- likelihood construction;
- Bayesian weighting;
- posterior inference;
- trajectory ranking;
- drift analysis;
- endpoint interpretation;
- crash-location interpretation.

Those belong to later inference layers.

## Merge rule

```text
merge only after evidence identity and provenance ordering are frozen,
not merely after assembly logic passes
```
