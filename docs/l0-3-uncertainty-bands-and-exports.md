# L0.3 Deterministic Slant-Range Uncertainty Bands and Exports

## Status

L0.3 extends the merged L0.2 Earth-surface locus generator with deterministic lower, nominal, and upper slant-range loci and canonical text exports.

This layer produces bounded geometry only. It does not validate published BTO arcs, rank hypotheses, recommend search areas, or make location claims.

## Dependency chain

```text
L0.0 WGS84 geometry primitives
        ↓
L0.1 satellite position and slant range
        ↓
L0.2 Earth-surface locus generation
        ↓
L0.3 uncertainty bands and exports
        ↓
Issue #7 published BTO arc validation
```

L0.3 depends on the existing L0.2 `generate_surface_locus` contract. It must not introduce a second Earth model, range model, or root solver.

## Geometric contract

For declared nominal range `r` and non-negative timing-derived range uncertainty `u`:

```text
lower_range_m = r - u
nominal_range_m = r
upper_range_m = r + u
```

The implementation fails closed when:

```text
lower_range_m <= 0
```

Satellite-position bias is recorded separately as metadata. It does not alter the timing-derived lower, nominal, or upper ranges in L0.3.

## Public uncertainty contracts

`SlantRangeUncertainty`

- immutable;
- validates positive finite nominal range;
- validates non-negative finite timing uncertainty;
- validates non-negative finite satellite-position bias metadata;
- exposes deterministic lower and upper range properties;
- returns ranges in canonical `lower`, `nominal`, `upper` order.

`SlantRangeBand`

- immutable;
- identifies one band as `lower`, `nominal`, or `upper`;
- binds the declared target range to one L0.2 `SurfaceLocusResult`;
- rejects mismatched target-range metadata.

`SlantRangeUncertaintyBands`

- immutable;
- requires exactly three bands in canonical order;
- requires band target ranges to match the uncertainty specification;
- requires all loci to use the same satellite position.

`generate_uncertainty_bands`

- calls `generate_surface_locus` once for each canonical range;
- forwards the declared L0.2 tolerance, stepping, bounds, and iteration controls;
- returns one immutable ordered result.

## Canonical CSV export

`export_uncertainty_bands_csv` returns UTF-8-compatible text with a fixed header and stable row order.

Canonical columns:

```text
schema
schema_version
band
point_index
longitude_deg
latitude_deg
altitude_m
target_range_m
tolerance_m
timing_range_uncertainty_m
satellite_position_bias_m
```

Rows are emitted in this order:

1. lower band points;
2. nominal band points;
3. upper band points.

Within each band, the existing L0.2 point order is preserved. Point indexes start at zero for each band.

Numeric values use a stable decimal representation without exponent notation. Line endings are `\n`.

## Canonical GeoJSON export

`export_uncertainty_bands_geojson` returns one GeoJSON `FeatureCollection`.

Each locus point is represented as a `Point` feature with coordinates in this order:

```text
[longitude_deg, latitude_deg, altitude_m]
```

Altitude is always explicitly `0.0`.

Feature properties contain:

- band identity;
- point index;
- target range in metres;
- solver tolerance in metres.

Collection metadata contains:

- schema and schema version;
- canonical band order;
- coordinate order;
- nominal range;
- timing-derived range uncertainty;
- separately declared satellite-position bias;
- satellite measurement epoch copied from the immutable input object.

JSON keys are sorted and compact separators are used. Non-finite JSON numbers are rejected.

## Determinism requirements

For identical immutable inputs, L0.3 must produce identical:

- uncertainty bounds;
- band ordering;
- locus ordering;
- CSV text;
- GeoJSON text.

The exports contain no generated timestamps, UUIDs, random identifiers, filesystem paths, network-derived values, or environment-dependent ordering.

The satellite epoch is not generated during export. It is copied from the already-declared satellite-position input.

## Failure behavior

L0.3 rejects:

- non-numeric values;
- Boolean values where real numbers are required;
- non-finite ranges or uncertainties;
- negative timing uncertainty;
- negative satellite-position bias metadata;
- non-positive lower range;
- invalid band identity;
- incorrect band order;
- mismatched target-range metadata;
- loci derived from different satellite positions;
- incorrect export input types.

Failures raise explicit `TypeError` or `ValueError` exceptions. The layer does not repair, infer, weight, or probabilistically reinterpret invalid inputs.

## Explicit exclusions

L0.3 does not perform:

- raw BTO ingestion;
- conversion from source timing observations into uncertainty values;
- source or provenance registration;
- published BTO arc comparison;
- benchmark validation;
- plotting or map rendering;
- BFO processing;
- aircraft dynamics or trajectory construction;
- debris drift modelling;
- weighting, confidence scoring, ranking, or Bayesian inference;
- endpoint selection;
- search-area recommendation;
- crash-location claims;
- clock-bias estimation;
- causal inference authority.

Published arc validation remains in Issue #7. Source ingestion and provenance remain in Issue #9.

## Files

```text
src/mh370_inverse_inference/satcom/uncertainty.py
src/mh370_inverse_inference/satcom/export.py
tests/satcom/test_uncertainty_bands.py
tests/satcom/test_locus_exports.py
docs/l0-3-uncertainty-bands-and-exports.md
```

The public contracts are re-exported from:

```text
src/mh370_inverse_inference/satcom/__init__.py
```

## Verification gate

Before merge, the branch must pass:

```text
Ruff
Black
mypy
pytest
DX.2
```

Issue: #4
