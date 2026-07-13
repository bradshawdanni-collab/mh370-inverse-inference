# L7.4 — Admissibility Decision Release Freeze

## Release identity

- Version: `1.0.0`
- Tag: `l7-v1.0.0`
- Status: `FROZEN`

## Frozen public surface

The L7 release freezes the following deterministic contracts:

1. `AdmissibilityDecisionRequest` — L7.0
2. `AdmissibilityDecisionRecord` — L7.1
3. `AdmissibilityDecisionResult` — L7.2
4. `AdmissibilityDecisionTrace` — L7.3

## Release artifacts

- `src/mh370_inverse_inference/admissibility/release.py`
- `release/l7-release-manifest.json`
- `tests/fixtures/admissibility/l7_4_release_case_001.json`
- `tests/admissibility/test_admissibility_release_freeze.py`

The canonical replay fixture is locked by SHA-256:

```text
386b6df436923005da7ddee39f1cac8b58279f483eff101ed05f5ac1a9f676f8
```

## Frozen guarantees

The release preserves exact ordered lineage from L6 comparative results and traces through L7 request, record, result, and trace identities. Every public object remains immutable, canonical, content-addressed, and replayable.

The release does not introduce probability, confidence, weighting, ranking, Bayesian semantics, trajectory, drift, endpoint, location, search-area, causal authority, clocks, UUIDs, randomness, filesystem authority, network authority, persistence, registries, or execution authority.

## Publication gate

Before publication:

1. Ruff must pass.
2. Black must pass.
3. mypy must pass.
4. pytest must pass.
5. DX.2 must pass.
6. The release-freeze pull request must merge to `main`.
7. Tag `l7-v1.0.0` must be created from the merged release commit.
8. The GitHub release must be published from that tag.

After publication, umbrella issue #152 may be closed as completed.
