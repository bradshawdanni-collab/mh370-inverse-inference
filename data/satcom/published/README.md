# Published BTO validation data

## Purpose

This directory is reserved for fixed, repository-local MH370 BTO arc benchmark fixtures used by the L0.4 deterministic validation layer.

A fixture in this directory is a validation input. It is not an inference result, probability surface, search-area recommendation, or crash-location claim.

## Current admission state

No published BTO benchmark fixture is currently admitted.

Do not add `benchmark_fixture.csv`, published coordinates, or a checksum declaration until a source has passed the source-admission process governed by Issue #9. Synthetic coordinates used in tests are test inputs only and must never be represented as published MH370 evidence.

## Source-admission gate

A benchmark fixture may be committed only after an authoritative source record declares all of the following:

- a stable source-artifact identifier;
- publisher and publication title;
- source location or citation;
- publication date, when available;
- retrieval date;
- licence, usage terms, or a documented access basis;
- the exact repository fixture filename;
- the exact lowercase SHA-256 digest of the committed fixture bytes;
- transformation history from the source artifact to the fixture;
- coordinate reference system and units;
- uncertainty and limitation notes;
- an explicit admission status;
- the benchmark identifier consumed by the validation code.

Issue #9 remains the authority for source ingestion, provenance registration, and admission decisions. This README defines the L0.4 consumer contract only; it does not admit a source or create a parallel provenance authority.

## Canonical CSV schema

An admitted fixture must be valid UTF-8 CSV with this exact header and column order:

```csv
point_id,sequence_index,longitude_deg,latitude_deg,altitude_m
```

No columns may be missing, added, or reordered.

### `point_id`

- non-empty text;
- unique within the fixture;
- no leading or trailing whitespace;
- stable across repeated validation runs.

### `sequence_index`

- zero-based ASCII decimal integer;
- canonical representation with no sign or leading zeros, except the value `0`;
- contiguous and ordered exactly as `0, 1, 2, ...`.

### `longitude_deg`

- finite decimal number in degrees;
- range `[-180, 180)`;
- no `NaN`, positive infinity, or negative infinity;
- no leading or trailing whitespace.

### `latitude_deg`

- finite decimal number in degrees;
- range `[-90, 90]`;
- no `NaN`, positive infinity, or negative infinity;
- no leading or trailing whitespace.

### `altitude_m`

- finite decimal number in metres;
- numerically equal to zero for every benchmark point;
- no leading or trailing whitespace.

## Byte-preservation and checksum rule

The fixture is consumed as immutable bytes.

Before any CSV parsing occurs, `load_published_bto_benchmark_csv(...)` computes the SHA-256 digest of those bytes and compares it with the declared expected digest. A mismatch fails closed.

Line endings, numeric spelling, row order, and final-newline state are therefore part of the admitted artifact. They must not be silently normalized after the checksum is declared.

## Fail-closed parsing rules

The loader rejects:

- an empty fixture;
- invalid UTF-8;
- a changed checksum;
- a byte-order mark or any other header mutation that changes the canonical columns;
- missing, additional, or reordered columns;
- blank rows;
- missing field values;
- surrounding field whitespace;
- duplicate point identifiers;
- non-canonical or unordered sequence indices;
- malformed or non-finite coordinates;
- longitude or latitude outside the declared ranges;
- non-zero altitude.

No rejected fixture may be partially loaded or silently repaired.

## Repository and network boundary

L0.4 loads repository-local bytes only. It must not:

- retrieve benchmark data from the network;
- select among competing sources;
- infer provenance from filenames;
- transform or interpolate source coordinates during loading;
- rewrite fixture bytes;
- assign evidentiary authority.

## Required fixture admission sequence

After Issue #9 has admitted a source:

1. produce the canonical CSV using the declared transformation history;
2. freeze the exact bytes;
3. compute the lowercase SHA-256 digest;
4. register the filename, digest, benchmark identifier, and source linkage under the Issue #9 authority;
5. commit the fixture without subsequent normalization;
6. add deterministic validation tests against the admitted checksum;
7. document assumptions and limitations in the L0.4 validation document.

Until that sequence is complete, this directory must remain without a published benchmark coordinate fixture.
