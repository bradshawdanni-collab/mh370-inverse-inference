# L0.1 Satellite Position and Slant Range

## Status

Implementation slice for Issue #167 under the L0 SATCOM geometry program in Issue #2.

## Contract

L0.1 adds two deterministic primitives:

- `SatellitePosition`, an immutable validated wrapper around an ECEF coordinate and declared epoch metadata;
- `slant_range_m`, a straight-line distance calculation from one validated ECEF point to one validated satellite position.

The implementation reuses the L0.0 `ecef_distance_m` primitive. It introduces no independent distance model.

## Validation

`SatellitePosition` rejects:

- non-string epoch metadata;
- empty epoch metadata;
- non-`ECEFPoint` values;
- the ECEF origin;
- non-finite coordinates through the underlying `ECEFPoint` contract.

`slant_range_m` rejects values outside its declared types and returns a deterministic non-negative distance in metres.

## Explicit exclusions

This slice does not implement:

- BTO arc generation;
- Earth-surface locus solving;
- uncertainty bands;
- exports;
- published arc validation;
- BFO processing;
- aircraft dynamics;
- drift modelling;
- Bayesian inference, confidence scoring, weighting, ranking, endpoint selection, or crash-location claims;
- clock-bias estimation or causal inference authority.

## Verification

The tests cover immutability, metadata validation, finite-value rejection, origin rejection, equatorial and polar reference cases, agreement with the underlying ECEF distance primitive, symmetry of that primitive, zero distance, and invalid input types.

Required gates are Ruff, Black, mypy, pytest, and DX.2.
