# Published BTO validation data

This directory contains source-bounded MH370 BTO reference data admitted for deterministic validation.

An admitted file must have a corresponding record in `source_register.yaml` that includes:

- stable artifact and benchmark identifiers;
- publisher and publication title;
- source URL and retrieval date;
- publication date where available;
- SHA-256 checksum;
- licence or usage terms;
- provenance and transformation history;
- uncertainty and limitation notes;
- coordinate reference system and units where applicable;
- admission status.

## Admitted seventh-arc fixture

`benchmark_fixture.csv` is admitted under benchmark ID `mh370-seventh-arc-published-bto-v1` for Issue #7 deterministic validation consumption.

Exact schema:

```text
point_id,sequence_index,longitude_deg,latitude_deg,altitude_m
```

The fixture is a deterministic sampled WGS84 zero-ellipsoidal-height locus derived from frozen published-source inputs. Its coordinates are not directly published coordinates and must not be represented as an inferred aircraft location, ranked endpoint, search recommendation, or crash-location claim.

The exact fixture bytes, SHA-256, sampling rule, independent sequence review, and final admission review are recorded in `source_register.yaml` and the associated provenance artifacts.
