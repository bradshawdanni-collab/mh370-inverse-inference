# Aircraft Dynamics Contracts

## L1.1 State and identity

L1.1 defines immutable aircraft state, control, request, and result records. Canonical JSON and SHA-256 establish stable identity.

## L1.2 Deterministic propagator

L1.2 implements one pure fixed-step transition:

```text
validated request
    → deterministic state transition
    → immutable step result
    → canonical hashes
```

The operation order is fixed:

1. resolve true airspeed;
2. apply altitude change;
3. apply heading change;
4. calculate great-circle angular distance;
5. calculate latitude;
6. calculate longitude;
7. construct the normalized immutable state;
8. compute metrics and canonical hashes.

Heading and longitude are normalized exactly once when the next state is constructed. Intermediate values are not rounded.

### Floating-point policy

- Public numeric inputs reject `NaN` and infinity.
- `dt_seconds` is finite and strictly positive.
- Python binary64 values are preserved in canonical JSON.
- Tolerances are used only for scientific assertions.
- Canonical bytes and hashes are exact identity artifacts.
- Cross-platform bitwise identity requires a controlled runtime.

```python
ABS_TOL = 1e-12
REL_TOL = 1e-12
```

### Audit identity

Each `DynamicsStepResult` contains the contract and model versions, stage index, operation, timestep, prior state, control, next state, metrics, and three SHA-256 identity hashes.

Execution duration may be recorded by an external trace adapter, but it does not participate in state identity or replay hashes.

### Regression fixtures

The fixed-step baseline covers straight-level, climb, and turning motion.

Approximate comparison validates physical quantities. Exact canonical bytes and hashes establish identity.

## L1.3 Reachability envelope

L1.3 applies bounded deterministic control sweeps to the L1.2 propagator and emits immutable reachable-state summaries, lineage indices, envelope metadata, and canonical identity hashes.

The reachability layer computes state-space evidence. It does not interpret observations or assign probabilities.

## L1.4 Reachability trace adapter

L1.4 is a structural translation layer:

```text
ReachabilitySummary
    → ReachabilityTraceAdapter
    → TraceMetricRecord
```

The adapter preserves the L1.3 `input_hash`, `output_hash`, and `op_signature_hash` exactly. It uses `TraceMetricRecord.from_parts(...)` as the only trace-hash construction path.

Required mappings are:

```text
stage_id = summary.operation
stage_index = explicit adapter argument
record_count = summary.reachable_state_count
hypothesis_count = None
normalization_error = None
pre_normalization_mass = None
status = ok
```

Reachability diagnostics are carried through canonical `metadata_json`, including contract version, model version, timestep, step count, control count, state count, constraint-violation count, and envelope metadata.

`duration_ms` is optional execution metadata. Changing it does not alter the source identity hashes or the composed trace hash.

The governing rule is:

```text
the adapter translates evidence;
it does not recompute the model
```

## Scope boundary

This layer excludes new propagation or reachability algorithms, route search, uncertainty sampling, satellite-observation evaluation, probabilistic weighting, drift analysis, and interpretive conclusions.
