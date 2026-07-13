# L6.4 — Comparative Assessment Release Freeze

## Status

The deterministic L6 comparative-assessment layer is complete and frozen as release `l6-v1.0.0`.

```text
ComparativeAssessmentRequest
        ↓
ComparativeAssessmentRecord
        ↓
ComparativeAssessmentResult
        ↓
ComparativeAssessmentTrace
        ↓
L6 release freeze
```

## Frozen surface

| Contract | Version |
|---|---:|
| `ComparativeAssessmentRequest` | L6.0 |
| `ComparativeAssessmentRecord` | L6.1 |
| `ComparativeAssessmentResult` | L6.2 |
| `ComparativeAssessmentTrace` | L6.3 |

The release metadata is defined in:

```text
src/mh370_inverse_inference/comparative/release.py
```

The machine-readable release manifest is:

```text
release/l6-release-manifest.json
```

## Canonical replay fixture

The canonical replay fixture is:

```text
tests/fixtures/comparative/l6_4_release_case_001.json
```

Its exact bytes are locked by SHA-256:

```text
8227573931afe760cdd394a531b21d17608384a82518f8026a624f3f56b00e52
```

The replay test independently recomputes the canonical hashes for the request, each record, the aggregate result, and the trace.

## Release identity

```text
Version: 1.0.0
Tag: l6-v1.0.0
Status: FROZEN
```

## Stability rule

After publication, the L6.0–L6.3 contracts are immutable. Any incompatible semantic or payload change requires a new contract version and a new release line. Existing canonical payloads, hashes, and replay fixtures remain valid historical artifacts.

## Excluded authority

This release does not establish probability, confidence, weighting, ranking, Bayesian inference, trajectory, drift, endpoint, location, search-area, causal, clock, UUID, randomness, filesystem, network, persistence, or registry authority.

It freezes only the deterministic structural comparison surface.
