# L0.2 Earth-Surface Slant-Range Locus Generation

## Status

Implementation slice for Issue #169 under the L0 SATCOM geometry program in Issue #2.

## Contract

L0.2 adds deterministic generation of zero-altitude WGS84 surface points whose straight-line ECEF distance to one validated `SatellitePosition` matches one declared target range within an explicit tolerance.

The public contract consists of:

- `SurfaceLocusPoint` — immutable paired geodetic and ECEF coordinates;
- `SurfaceLocusResult` — immutable ordered points plus declared solver metadata;
- `generate_surface_locus` — bounded longitude sampling, latitude bracketing, and deterministic bisection refinement.

## Reused primitives

The implementation reuses:

- `GeodeticPoint` and `geodetic_to_ecef` from L0.0;
- `SatellitePosition` and `slant_range_m` from L0.1.

It introduces no independent Earth model or distance model.

## Geometric invariant

Every emitted point satisfies:

```text
point.geodetic.altitude_m == 0.0
point.ecef == geodetic_to_ecef(point.geodetic)
abs(slant_range_m(point.ecef, satellite) - target_range_m) <= tolerance_m
```

## Determinism

Identical inputs produce identical ordered tuples. Points are ordered by normalized longitude and then latitude. Duplicate coordinates are suppressed deterministically.

## Validation

The solver rejects:

- non-`SatellitePosition` inputs;
- non-finite, zero, or negative ranges, tolerances, and sampling steps;
- invalid latitude and longitude bounds;
- non-positive iteration limits;
- inconsistent locus-point coordinate pairs.

A geometrically valid request with no matching surface point returns an empty tuple rather than failing.

## Explicit exclusions

This slice does not implement:

- conversion from timing measurements to range;
- uncertainty bands;
- published arc validation;
- mapping, plotting, GeoJSON, or CSV export;
- aircraft dynamics or trajectory construction;
- probability, weighting, ranking, endpoint selection, search-area recommendation, or location claims;
- clock-bias estimation or causal inference authority.

## Verification

Tests cover deterministic repeatability, two-branch geometry, tangent samples, polar geometry, empty results, ordering, surface and tolerance invariants, and invalid inputs.

Required gates are Ruff, Black, mypy, pytest, and DX.2.
