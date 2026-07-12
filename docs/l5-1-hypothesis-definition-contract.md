# L5.1 — Hypothesis definition contract

L5.1 defines a neutral, immutable `HypothesisDefinition` that can be referenced by the L5.0 evaluation request without performing evaluation.

## Contract flow

```text
HypothesisDefinition
    -> hypothesis_id
    -> HypothesisEvaluationRequest.ordered_hypothesis_ids
```

L5.1 does not modify `HypothesisEvaluationRequest`. It establishes a deterministic source for admissible hypothesis identities.

## Contract fields

A definition contains only:

- `hypothesis_id`
- `hypothesis_schema_version`
- `hypothesis_type`
- `statement`
- `ordered_assumption_ids`
- `definition_hash`

The public constructor is disabled. Definitions are created only through `build_hypothesis_definition`.

## Neutral classifications

The initial allowlist is:

- `DESCRIPTIVE`
- `RELATIONAL`
- `CONSTRAINT`

These values classify structure only. They do not represent likelihood, confidence, ranking, causation, routes, coordinates, endpoints, or search areas.

## Canonical identity

`definition_hash` is produced through the repository `sha256_payload` helper from:

```text
hypothesis_schema_version
hypothesis_type
statement
ordered_assumption_ids
```

Assumption order is identity-bearing. `hypothesis_id` equals `definition_hash`, avoiding UUIDs and stateful identity.

## Boundary

The contract performs no registry lookup, evidence reconstruction, request reconstruction, persistence, caching, environment access, filesystem access, network access, time access, or random generation.

Evaluation semantics remain deferred to later L5 milestones.
