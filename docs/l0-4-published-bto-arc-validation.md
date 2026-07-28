# L0.4 Deterministic Published BTO Arc Validation

## Status

Issue #172 is complete and the repository-local seventh-arc benchmark is admitted on `main`.

L0.4 consumes that exact admitted fixture and validates the existing deterministic WGS84 surface-locus implementation against it. This layer does not retrieve source material, recalculate source provenance, ingest raw BTO records, or create a competing evidence authority.

## Admitted benchmark

Benchmark ID:

```text
mh370-seventh-arc-published-bto-v1
```

Fixture:

```text
data/satcom/published/benchmark_fixture.csv
```

Frozen SHA-256:

```text
3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7
```

Point count: `176`.

Exact schema:

```csv
point_id,sequence_index,longitude_deg,latitude_deg,altitude_m
```

The fixture is `DERIVED_FROM_PUBLISHED_EVIDENCE`. Its coordinates are not directly published coordinates and are not an inferred aircraft path, ranked endpoint, search area, or crash-location claim.

## Dependency chain

```text
L0.0 WGS84 geometry primitives                 complete
        ↓
L0.1 satellite position and slant range        complete
        ↓
L0.2 Earth-surface locus generation            complete
        ↓
L0.3 uncertainty bands and canonical exports   complete
        ↓
L0.4A benchmark source admission (#172)        complete
        ↓
L0.4 published BTO arc validation              active
```

## Purpose

L0.4 is a deterministic comparison and reporting boundary. It answers one bounded question: given the admitted benchmark bytes and one generated L0.2 surface locus produced under the matching frozen geometry configuration, what are the ordered positional deviations?

It does not infer a trajectory or assign evidential probability.

## Public contracts

The SATCOM package exposes:

- `ADMITTED_SEVENTH_ARC_BENCHMARK_ID`;
- `ADMITTED_SEVENTH_ARC_FIXTURE_SHA256`;
- `PublishedBTOBenchmarkPoint`;
- `PublishedBTOBenchmark`;
- `BTOValidationSample`;
- `BTOValidationResult`;
- `BTO_POINT_MATCHING_CONFIGURATION_ID`;
- `load_published_bto_benchmark_csv(...)`;
- `load_admitted_seventh_arc_benchmark(...)`;
- `compare_published_bto_benchmark(...)`;
- `serialize_bto_validation_result_json(...)`.

The benchmark, sample, and result contracts are frozen and slotted dataclasses. Invalid or ambiguous inputs fail closed.

## Fixture-consumption rule

`load_admitted_seventh_arc_benchmark(...)` accepts bytes only when their lowercase SHA-256 equals the Issue #172 admitted digest.

The generic loader also requires:

- UTF-8;
- LF line endings;
- a final LF newline;
- the exact canonical header and column order;
- no blank rows;
- no missing values or surrounding field whitespace;
- unique point identifiers;
- unique coordinates;
- contiguous zero-based sequence indices;
- canonical longitude-then-latitude row order;
- finite coordinates;
- longitude within `[-180, 180)`;
- latitude within `[-90, 90]`;
- altitude exactly `0.0` metres.

No rejected fixture is silently repaired, reordered, normalized, or rewritten.

## Generated-locus configuration

The admitted fixture was frozen from the already reviewed zero-height WGS84 range constraint. L0.4 validates the existing L0.2 `generate_surface_locus(...)` implementation using the same deterministic geometry target rather than regenerating source provenance.

The integration test uses the frozen target state and target range already established upstream:

```text
epoch_utc: 2014-03-08T00:19:29.416Z
satellite_ecef_m: 18178354.27195026, 38050848.06484729, 393043.6546171822
target_range_m: 37861969.39520467
surface: WGS84 ellipsoidal height 0 m
longitude domain: [-180, 180)
longitude step: 1 degree
latitude bracket step: 0.25 degree
slant-range stopping tolerance: 0.01 m
maximum bisection iterations: 80
```

These values are consumed as already frozen upstream inputs. L0.4 does not reinterpret their provenance or derive them from raw SATCOM timing.

## Point-matching rule

The only supported configuration is:

```text
sequence-index-aligned-geodesic-v1
```

Benchmark point `i` is matched only with generated `SurfaceLocusPoint` `i`.

The generated sequence must:

- contain exactly the same number of points as the benchmark;
- contain only validated zero-altitude `SurfaceLocusPoint` objects;
- remain in canonical longitude-then-latitude order.

No nearest-neighbour search, interpolation, weighting, remapping, branch selection, or hidden alignment is performed.

## Deviation metric

Each validation sample records the WGS84 ellipsoidal surface distance in metres between its aligned benchmark and generated geodetic coordinates.

For ordered deviations `d_0 ... d_(n-1)`:

```text
sample_count = n
maximum_deviation_m = max(d_i)
mean_deviation_m = fsum(d_i) / n
```

The result also records:

- `benchmark_id`;
- `fixture_sha256`;
- `model_version`;
- `configuration_id`;
- ordered per-point samples.

Construction rejects result objects whose count, maximum, or mean does not exactly agree with the contained samples.

## Machine-readable output

`serialize_bto_validation_result_json(...)` emits deterministic UTF-8 JSON with:

- sorted object keys;
- no generated timestamp or UUID;
- explicit metre units;
- benchmark and configuration metadata;
- maximum and mean deviation;
- sample count;
- ordered point IDs, sequence indices, and deviations;
- one final LF newline.

Identical inputs produce identical output bytes.

## Failure behavior

Validation fails closed on checksum mismatch, malformed serialization, duplicate or unordered benchmark data, non-finite coordinates, non-zero benchmark altitude, generated-count mismatch, unsupported point-matching configuration, non-canonical generated ordering, negative/non-finite deviations, or inconsistent result summaries.

## Governance boundary

L0.4 does not add or perform:

- network source retrieval;
- source admission or provenance reassignment;
- raw BTO ingestion or timing conversion;
- BFO processing;
- aircraft dynamics or trajectory construction;
- debris drift modelling;
- plotting or map rendering;
- probability, confidence, weighting, ranking, Bayesian inference, endpoint selection, or search-area recommendation;
- clock-bias estimation or causal inference;
- geographic or crash-location claims;
- changes to the L0.0-L0.3 geometry contracts.

The admitted benchmark exists only to validate a deterministic geometry implementation against a fixed, source-bounded reference artifact.

## Completion gate

L0.4 is complete only when the admitted fixture is consumed without mutation, deterministic comparison and JSON serialization tests pass, the integration validation runs against all 176 admitted points, and Ruff, Black, mypy, pytest, and DX.2 are green.
