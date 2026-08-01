# L2.1 Deterministic BFO Component Model

## Purpose

This milestone decomposes one governed BFO observation into explicit deterministic frequency contributions while preserving the L2.0 source and calibration boundary.

## Inputs

The component model requires:

- an `ADMITTED` `BFOObservation`;
- an `ADMITTED` `BFOComponentInputs` record;
- declared reference frequency and speed-of-light constants;
- source and version identifiers for the declared constants;
- a versioned model identity.

## Canonical component order

1. `SATELLITE_MOTION`
2. `AIRCRAFT_MOTION`
3. `EARTH_ROTATION_REFERENCE_FRAME`
4. `FIXED_CALIBRATION`

The predicted BFO is the deterministic sum of those four terms. The residual is:

```text
observed_bfo_hz - predicted_bfo_hz
```

The result records whether the absolute residual is within the governed observation uncertainty.

## Provenance

The result preserves:

- observation source artifact and version;
- calibration source and version;
- constants source and version;
- component-model version.

## Fail-closed rules

Evaluation rejects:

- non-governed observation or input types;
- unsupported contract versions;
- non-admitted observations;
- non-admitted component inputs;
- non-finite component values;
- non-positive declared constants;
- missing source, version, or model identifiers.

## Exclusions

This contract does not:

- invert BFO into a trajectory;
- select aircraft velocity;
- rank candidate paths or hypotheses;
- combine BFO with debris or search evidence;
- infer an endpoint or search area;
- make a crash-location claim.
