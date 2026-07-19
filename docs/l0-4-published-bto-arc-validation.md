# L0.4 Deterministic Published BTO Arc Validation

## Status

L0.4 is implemented only through its fixture contracts, checksum-verified CSV loader, deterministic comparison rule, metrics contracts, synthetic tests, package exports, and boundary documentation.

No published BTO benchmark fixture is currently admitted. Therefore this branch does not yet contain a completed published-reference validation result and makes no claim that generated MH370 BTO loci agree with any published arc.

Issue #172, **L0.4A admit published BTO benchmark source and fixture**, must admit the exact source, transformation record, repository-local fixture bytes, benchmark identifier, and SHA-256 digest before final L0.4 validation can occur.

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
L0.4A benchmark source admission               pending in Issue #172
        ↓
L0.4 published BTO arc validation              pending admitted fixture
```

## Purpose

L0.4 validates deterministic SATCOM geometry against one fixed, admitted, repository-local published-reference benchmark.

It is a comparison and reporting layer only. It does not infer a flight path, rank candidate locations, select an endpoint, estimate probability, or make a crash-location claim.

## Public contracts

The SATCOM package exposes:

- `PublishedBTOBenchmarkPoint`;
- `PublishedBTOBenchmark`;
- `BTOValidationSample`;
- `BTOValidationResult`;
- `BTO_POINT_MATCHING_CONFIGURATION_ID`;
- `load_published_bto_benchmark_csv(...)`;
- `compare_published_bto_benchmark(...)`.

The benchmark, sample, and result objects are frozen and slotted dataclasses. Their validation rules fail closed rather than normalizing malformed inputs.

## Benchmark fixture contract

An admitted fixture must be supplied as immutable bytes and must use this exact UTF-8 CSV header and column order:

```csv
point_id,sequence_index,longitude_deg,latitude_deg,altitude_m
```

The fixture loader verifies the declared lowercase SHA-256 digest before parsing.

The loader rejects:

- a checksum mismatch;
- invalid UTF-8;
- an empty fixture;
- blank rows;
- missing, additional, or reordered columns;
- missing values;
- surrounding field whitespace;
- duplicate point identifiers;
- non-canonical or unordered sequence indices;
- malformed or non-finite coordinates;
- longitude outside `[-180, 180)`;
- latitude outside `[-90, 90]`;
- non-zero altitude.

The exact bytes, including line endings, numeric spelling, row order, and final-newline state, are part of the admitted artifact.

## Source-admission boundary

L0.4 does not retrieve or select external sources.

Issue #172 must establish, at minimum:

- the authoritative source identity and citation;
- publisher and publication metadata;
- retrieval date;
- licence, terms, or documented access basis;
- coordinate reference system and units;
- extraction and transformation history;
- assumptions, limitations, and uncertainty notes;
- the exact fixture filename;
- the exact fixture SHA-256 digest;
- a stable benchmark identifier;
- an explicit admission state.

Issue #9 remains the broader provenance, attribution, registry, and evidence-use milestone after the minimum L0.4A admission step.

Synthetic coordinates used by tests are code-path fixtures only. They are not published MH370 evidence and must never be described as such.

## Point-matching rule

The only admitted comparison configuration is:

```text
sequence-index-aligned-geodesic-v1
```

For a benchmark containing points `0..n-1`, benchmark point `i` is matched only with generated `SurfaceLocusPoint` `i`.

Generated points must:

- be supplied as a tuple;
- contain only validated `SurfaceLocusPoint` objects;
- have the same count as the benchmark;
- remain in canonical longitude-then-latitude order;
- have zero altitude through the existing L0.2 contract.

No nearest-neighbour search, interpolation, weighting, remapping, or hidden alignment is performed by this L0.4 contract.

## Deviation metric

Each sample records the WGS84 ellipsoidal surface distance in metres between the aligned benchmark and generated geodetic points.

For deviations `d_0, d_1, ..., d_(n-1)`:

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

Result construction rejects summaries whose sample count, maximum, or mean does not exactly match the supplied ordered samples.

## Determinism

Identical benchmark objects, generated points, model version, and configuration ID produce equal immutable results.

The implementation introduces no generated timestamps, UUIDs, randomness, network access, filesystem discovery, ranking, confidence scores, or probability values.

## Failure behavior

Validation fails closed on:

- wrong object types;
- blank identifiers or metadata;
- invalid fixture checksums;
- malformed fixtures;
- ambiguous or non-canonical ordering;
- benchmark/generated count mismatch;
- unsupported matching configuration;
- non-finite or negative deviations;
- inconsistent result metrics.

No rejected input is partially loaded, silently repaired, or automatically reordered.

## Current test boundary

The committed tests use only synthetic repository-local values to verify:

- immutable contracts;
- fixture checksum enforcement;
- canonical CSV parsing;
- malformed-input rejection;
- exact sequence-index alignment;
- WGS84 deviation calculation;
- maximum, mean, and sample-count reporting;
- deterministic replay;
- metadata and ordering enforcement.

These tests verify implementation behavior. They do not validate against published MH370 coordinates.

## Explicit exclusions

L0.4 does not add:

- network source retrieval;
- source-authority assignment outside Issue #172 and Issue #9;
- raw BTO ingestion or timing conversion;
- BFO processing;
- aircraft dynamics or trajectory construction;
- debris-drift modelling;
- plotting or map rendering;
- probability, confidence, weighting, ranking, Bayesian inference, endpoint selection, or search-area recommendation;
- clock-bias estimation or causal inference;
- geographic or crash-location claims;
- changes to the L0.0-L0.3 geometry contracts.

## Remaining completion gates

Before the L0.4 pull request can be considered complete:

1. Issue #172 must admit one real published-reference fixture and checksum.
2. The exact admitted fixture and source register must be committed without silent normalization.
3. Deterministic validation must run against that fixture.
4. Machine-readable validation output must be finalized and tested.
5. Assumptions and limitations tied to the admitted source must be recorded.
6. Ruff, Black, mypy, pytest, and DX.2 must pass in GitHub Actions.

Until those gates are complete, the branch must remain unmerged and no published-reference agreement claim may be made.
