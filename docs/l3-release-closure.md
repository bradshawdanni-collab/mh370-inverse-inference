# L3 release closure

## Status

L3 is functionally complete and version-frozen at release version `1.0.0`.

The intended immutable release tag is:

```text
l3-v1.0.0
```

The tag must be created from `main` only after this closure change is merged and all required checks pass.

## Frozen authority-reduction chain

```text
RegisteredEvidenceRecord
    -> RegisteredEvidenceProjection
    -> AcceptedEvidenceProjection
    -> InterpretationRequest
    -> NeutralRuleExecution
    -> InterpretationResult
    -> TraceMetricRecord
```

Each arrow is one-way. No downstream contract may reconstruct registry authority, recover raw evidence, or widen the semantic scope of the input it receives.

## Frozen contract surface

| Contract | Version | Role |
|---|---:|---|
| Registered evidence consumption | `L3.0` | Reduces registered evidence into an accepted downstream projection |
| Interpretation request | `L3.1` | Canonicalizes and seals accepted projection lineage |
| Neutral derived claim | `L3.3` | Represents content-addressed structural claims only |
| Interpretation result | `L3.4` | Seals ordered lineage-valid neutral claims |
| Neutral rule execution | `L3.5` | Applies allowlisted deterministic neutral rules |
| Shared trace and replay | `L3.6` | Maps execution into the immutable shared trace contract |

The earlier L3.2 empty-result boundary remains part of repository history, but the active result contract is the backward-compatible L3.4 result envelope.

## Frozen runtime identifiers

```text
release_version: 1.0.0
release_tag: l3-v1.0.0
rule_version: 1.0.0
stage_id: L3.6-neutral-interpretation-execution
```

These values are declared in:

```text
src/mh370_inverse_inference/interpretation/release.py
release/l3-release-manifest.json
```

## Canonical replay baseline

The canonical L3 replay fixture is:

```text
tests/fixtures/interpretation/l3_6_replay_case_001.json
```

Its frozen SHA-256 digest is:

```text
870720bfe668309a0ef8448e64fb6dff1bd2683716257c597faea27c0d2738df
```

Any fixture change requires a new release version and an explicit replacement manifest. The existing fixture must not be silently rewritten.

## End-to-end release gate

The release integration test proves deterministic replay through the complete L3 chain. Identical admitted inputs and rule configuration must reproduce identical:

- request hashes;
- claim hashes;
- result hashes;
- operation-signature hashes;
- trace hashes.

## Permitted semantics

L3 may assert only allowlisted neutral structural facts, such as the presence of source, observation, validation, or consumed-evidence identities.

## Explicitly excluded semantics

L3 does not contain or authorize:

- probabilities, confidence, likelihoods, weights, or ranking;
- Bayesian fusion or substantive evidential inference;
- trajectory, drift, coordinates, routes, endpoints, or location conclusions;
- causal conclusions;
- registry lookup from downstream interpretation layers;
- raw-evidence reconstruction;
- timestamps, UUIDs, randomness, persistence, network access, or environment-derived state in deterministic payloads.

## Change-control rule

After `l3-v1.0.0` is created, any change to a frozen contract, rule definition, stage identifier, canonical fixture, canonical payload, or hash preimage requires:

1. a new issue describing the compatibility impact;
2. a new contract or release version;
3. updated replay fixtures and manifest;
4. complete CI and DX.2 validation;
5. a new immutable release tag.

## Closure statement

L3 is closed when the release-closure pull request is merged, checks pass on `main`, and tag `l3-v1.0.0` is created at that verified commit. Work after that point belongs to L4 or to a separately versioned L3 maintenance release.
