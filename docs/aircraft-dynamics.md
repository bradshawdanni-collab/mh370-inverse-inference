# L1.1 Aircraft Dynamics State and Identity Contract

L1.1 defines the aircraft-dynamics state and step records used by later deterministic propagation work. It is a state-and-identity contract layer, not a physics solver.

## Architectural rule

```text
simulation computes state
hashing canonically fingerprints inputs and outputs
tracing records the evidence
replay compares the evidence
```

## Layer separation

```text
AircraftState
    ↓
DynamicsStep / deterministic propagation
    ↓
DynamicsStepResult
    ↓
TraceMetricRecord adapter
```

The physics state remains testable without tracing. Tracing observes execution; it does not perform the simulation.

## Immutable records

L1.1 defines these immutable value objects:

- `AircraftState`
- `DynamicsControlInput`
- `DynamicsRequest`
- `DynamicsStepResult`

`AircraftState` contains timestamped aircraft identity data:

```text
timestamp_utc
latitude_deg
longitude_deg
altitude_m
true_airspeed_mps
heading_deg
mass_kg
model_version
```

`DynamicsRequest` contains the full deterministic input contract for a future propagation step:

```text
initial_state
control_input
dt_seconds
model_version
```

`DynamicsStepResult` records one transition:

```text
previous_state
next_state
control_input
dt_seconds
model_version
metrics
```

## Canonical serialization

Records serialize to canonical JSON using:

- stable key ordering;
- deterministic separators;
- JSON-compatible primitive values;
- explicit `model_version` in the hashed payload.

The implementation hashes canonical payloads using the existing L10 engine hashing utilities. Python object identity and memory layout are never hashed.

## Trace compatibility

Aircraft-dynamics records are designed to be consumed by a later trace adapter. The future adapter should emit the common trace core:

```text
stage_index
operation
input_hash
output_hash
op_signature_hash
duration_ms
record_count
```

Stage-specific values remain in `metrics`, for example:

```text
fuel_mass_kg
energy_error
constraint_violation
normalization_error
```

Bayesian-specific fields are not forced into the aircraft-dynamics state contract.

## Scope boundary

L1.1 does not implement aircraft propagation, fuel modelling, BFO inversion, Bayesian inference, debris drift, or endpoint-location conclusions. Those layers may depend on this contract later, but they do not belong inside it.
