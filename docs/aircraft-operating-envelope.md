# L1.2 Aircraft Operating Envelope Contract

## Purpose

L1.2 defines immutable, source-bounded aircraft operating limits only.

The contract version is fixed at `AIRCRAFT-ENVELOPE-1`.

## Contract fields

An `AircraftOperatingEnvelope` contains:

- minimum and maximum speed in metres per second;
- minimum and maximum altitude in metres;
- maximum climb rate in metres per second;
- maximum descent rate in metres per second;
- maximum turn rate in degrees per second;
- exact source artifact identifier and version;
- model/configuration version;
- provenance admission state;
- contract version.

All numerical values must be finite and non-negative. Minimum values cannot exceed their corresponding maximum values.

## Provenance boundary

The envelope is accepted only when its admission state is explicitly `PROPOSED` or `ADMITTED`. Other states fail closed.

The contract records the exact source identity and version. It does not select a source, infer authority, or promote a proposed source to admitted status.

## Scope boundary

This contract does not:

- propagate aircraft states;
- determine whether a transition is reachable;
- estimate fuel burn or remaining fuel;
- infer mass, wind, thrust, drag, or true airspeed;
- process BFO measurements;
- infer or rank trajectories;
- select an endpoint or search area;
- make a crash-location claim.

Deterministic propagation against an admitted envelope is a later bounded milestone.
