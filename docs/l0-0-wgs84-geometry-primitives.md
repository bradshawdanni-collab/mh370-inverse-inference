# L0.0 deterministic WGS84 geometry primitives

## Purpose

This milestone provides the bounded coordinate foundation required by Issue #2.
It defines deterministic WGS84 constants, validated geodetic and ECEF value
objects, coordinate conversion functions, longitude normalization, and direct
ECEF distance measurement.

## Public surface

```python
ECEFPoint
GeodeticPoint
geodetic_to_ecef
ECEFPoint
ecef_to_geodetic
ecef_distance_m
normalize_longitude_deg
```

The module also exports the WGS84 semi-major axis, semi-minor axis, flattening,
first eccentricity squared, and second eccentricity squared.

## Validation rules

- latitude must be finite and within `[-90, 90]` degrees;
- longitude must be finite and is normalized to `[-180, 180)`;
- altitude and all ECEF components must be finite;
- the ECEF origin is rejected because it has no unique geodetic coordinate;
- incorrect object types fail closed;
- identical inputs produce identical outputs.

## Coordinate conventions

Geodetic coordinates use decimal degrees and metres. ECEF coordinates use
metres in an Earth-centred, Earth-fixed Cartesian frame. No planar geometry is
introduced.

## Boundary

This milestone does not implement satellite position modelling, BTO
slant-range evaluation, Earth-surface loci, uncertainty bands, exports,
published arc validation, BFO analysis, aircraft dynamics, drift, Bayesian
inference, ranking, endpoint inference, or crash-location claims.

## Sequence

```text
L0.0 WGS84 primitives
        ↓
L0.1 satellite position and slant range
        ↓
L0.2 Earth-surface locus generation
        ↓
Issue #4 uncertainty bands and exports
        ↓
Issue #7 published BTO arc validation
```

## Verification

The milestone is complete only when Ruff, Black, mypy, pytest, and DX.2 pass.
Tests cover equatorial and polar cases, geodetic/ECEF round trips, longitude
normalization, deterministic distance calculation, finite-value rejection, and
invalid-type rejection.
