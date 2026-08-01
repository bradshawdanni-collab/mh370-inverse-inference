# L2.0 BFO Source and Calibration Contract

## Purpose

Freeze the governed identity and calibration metadata required for a Burst Frequency Offset observation before any BFO measurement modelling or inversion is admitted.

## Contract boundary

The contract records:

- observation identity;
- canonical UTC timestamp;
- BFO value in hertz;
- uncertainty in hertz;
- source artifact and version;
- source citation;
- calibration source and version;
- admission state;
- deterministic serialization.

## Fail-closed rules

The contract rejects:

- missing or blank identifiers;
- non-canonical timestamps;
- non-finite BFO or uncertainty values;
- negative uncertainty;
- units other than hertz;
- unsupported contract versions;
- invalid admission-state types.

## Explicit exclusions

L2.0 does not:

- invert BFO;
- estimate aircraft velocity;
- model satellite or ground-station Doppler components;
- rank trajectories or hypotheses;
- infer endpoints or search areas;
- make a crash-location claim.

## Admission posture

The source register remains `PROPOSED` until source artifacts, citations, calibration records, CI, and an independent reproduction review are complete.
