# L5.3 — Deterministic hypothesis evaluation result contract

L5.3 defines the first immutable result envelope for deterministic hypothesis evaluation.

## Contract flow

```text
HypothesisEvaluationRequest
    + EvidenceHypothesisRelationRecord(s)
    -> HypothesisEvaluationResult
```

The result preserves the exact L5.0 request identity, evaluation policy version, and ordered hypothesis identities. It records ordered relation-record identities, one structural outcome per hypothesis, an aggregate status, ordered reason codes, and a canonical result hash.

## Structural outcomes

The permitted outcomes are:

- `RETAINED`
- `REJECTED`
- `INSUFFICIENT_BASIS`
- `CONSTRAINT_BLOCKED`

These values are deterministic structural dispositions. They do not carry probability, confidence, weight, score, rank, route, endpoint, location, or search-area meaning.

## Lineage rules

Every relation record must:

- reference a hypothesis included in the exact request;
- reference a supporting or contradicting claim included in the matching request sequence;
- have a unique record hash within the result.

The ordered outcome sequence must align one-to-one with the ordered request hypothesis sequence.

## Canonical identity

`result_hash` is derived through the repository `sha256_payload` helper from:

- `request_hash`
- `evaluation_policy_version`
- ordered hypothesis IDs
- ordered relation-record hashes
- ordered outcomes
- aggregate status
- ordered reason codes
- `evaluation_result_contract_version`

The result hash is excluded from its own preimage.

## Boundary

L5.3 introduces no probabilities, posterior updates, confidence values, support strengths, rankings, Bayesian updates, routes, trajectories, drift models, coordinates, endpoints, locations, search-area recommendations, or causal conclusions. It performs no lookup, reconstruction, persistence, caching, filesystem, environment, or network operation.

The ordered evaluation trace remains deferred to L5.4.
