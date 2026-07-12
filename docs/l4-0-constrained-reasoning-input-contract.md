# L4.0 constrained evidential reasoning input contract

## Status

L4.0 opens the L4 phase with a deterministic authority-reduction boundary. It does not perform evidential reasoning.

## Governing transition

```text
InterpretationResult (L3.4)
    -> ConstrainedReasoningRequest (L4.0)
```

The transition is one-way. A reasoning request cannot reconstruct an interpretation result, registry record, accepted projection, or raw evidence object.

## Contract contents

`ConstrainedReasoningRequest` preserves only:

- the L3 interpretation result hash;
- the upstream interpretation input hash;
- the active interpretation contract version;
- ordered neutral claim hashes;
- the declared reasoning-policy version;
- the L4.0 contract version;
- a deterministic request hash.

The request hash is computed from canonical JSON using the repository hashing helper. Identical result content and policy version must produce an identical request.

## Construction rule

The only supported construction path is:

```python
build_constrained_reasoning_request(
    interpretation_result,
    reasoning_policy_version="reasoning-1.0.0",
)
```

The builder accepts only an exact `InterpretationResult`. Dictionaries, identifiers, registry records, projections, and arbitrary objects are rejected.

## Explicit exclusions

L4.0 introduces no:

- likelihoods, probabilities, confidence, weights, or rankings;
- Bayesian updates or hypothesis comparison;
- trajectory, drift, coordinate, route, endpoint, or location reasoning;
- causal conclusions;
- registry lookup or raw-evidence reconstruction;
- timestamps, UUIDs, randomness, filesystem, network, persistence, caching, or environment-derived state.

## Change control

L3 remains frozen at tag `l3-v1.0.0`. L4.0 depends on the public L3 result contract but does not modify any frozen L3 contract, fixture, manifest, hash preimage, or release identifier.

Any later evidential scoring or inference behavior requires a separately versioned L4 milestone with explicit mathematical semantics, validation fixtures, and failure rules.
