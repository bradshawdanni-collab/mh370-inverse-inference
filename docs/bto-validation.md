# Published BTO Arc Validation

## Objective

Validate generated BTO slant-range loci against admitted published MH370 reference data using deterministic, auditable metrics.

## Metrics

For every generated point, the current validator computes the nearest WGS84 geodesic distance to the admitted reference locus. The validation report includes:

- benchmark identifier,
- model version,
- sample count,
- mean deviation in metres,
- maximum deviation in metres.

## Data admission

Published reference data must be registered in `data/satcom/published/source_register.yaml` before use. The register records source identity, checksum, licence or terms, provenance, transformations, uncertainty, and admission status.

Synthetic fixtures used by unit tests validate only the software pathway. They are not official MH370 evidence and cannot satisfy Issue #7 by themselves.

## Assumptions

- Generated and reference coordinates use WGS84 latitude and longitude.
- Nearest-reference distance is a reproducible first validation metric.
- Point density and reference sampling can affect nearest-neighbour results and must be reported with each benchmark.
- Validation does not imply trajectory or crash-location inference.

## Limitations

- No published benchmark dataset has yet been admitted.
- Symmetric nearest-neighbour or curve-to-curve metrics may be needed to reduce sampling-direction bias.
- Benchmark-specific uncertainty envelopes and acceptance thresholds remain to be defined from authoritative source material.

## Completion gate

Issue #7 remains open until an authoritative published benchmark is admitted, transformed reproducibly, compared with the generated locus, and accompanied by documented mean and maximum deviation results.
