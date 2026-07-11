# L2.0 Canonical Observation Admission

L2.0 defines the first evidence-admission boundary.

```text
raw observation
    → canonical observation record
    → deterministic validation
    → ADMITTED | REJECTED | QUARANTINED
    → trace-compatible admission result
```

## Governing invariant

```text
admission establishes whether evidence may enter;
inference determines what the evidence means
```

## Contracts

The observations package defines immutable records for:

- observation values and types;
- source identity and provenance;
- uncertainty metadata;
- admission requests;
- admission results and reason codes.

BTO and BFO use the same admission engine while remaining distinct observation types.

## Deterministic validation order

1. Timestamp validity.
2. Measured-value finiteness.
3. Unit validity and type compatibility.
4. Uncertainty validity and unit consistency.
5. Source presence and identity.
6. Source hash validity.
7. Provenance status.
8. Model-version compatibility.
9. Contract-version compatibility.
10. Final admission status.

Hard structural failures produce `REJECTED`. Unresolved or missing provenance produces `QUARANTINED`. Fully valid observations produce `ADMITTED`.

## Identity and trace

Admission input, output, and operation-signature hashes use the existing canonical JSON and SHA-256 helpers. Admission traces are created only through `TraceMetricRecord.from_parts(...)`.

Execution duration is optional metadata and does not participate in identity hashes.

## Scope boundary

L2.0 performs no BTO geometry, BFO Doppler modelling, residual calculation, likelihood construction, Bayesian weighting, trajectory ranking, drift analysis, or endpoint interpretation.
