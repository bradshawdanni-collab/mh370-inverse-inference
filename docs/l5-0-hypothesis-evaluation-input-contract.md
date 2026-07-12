# L5.0 — Hypothesis evaluation input contract

L5.0 introduces a deterministic input boundary for later hypothesis evaluation without performing evaluation itself.

## Required flow

```text
ConstrainedReasoningResult
    + NeutralReasoningTrace
    -> HypothesisEvaluationRequest
```

The request preserves the exact L4 reasoning-result and trace identities, identifies the hypothesis schema and evaluation policy, and carries ordered hypothesis and claim identities.

## Contract fields

- `reasoning_result_hash`
- `reasoning_trace_hash`
- `hypothesis_schema_version`
- `evaluation_policy_version`
- `ordered_hypothesis_ids`
- `ordered_supporting_claim_hashes`
- `ordered_contradicting_claim_hashes`
- `evaluation_contract_version`
- `request_hash`

The request is frozen, slotted, content-addressed, and available only through `build_hypothesis_evaluation_request`.

## Canonical identity

`request_hash` is computed with the repository `sha256_payload` helper over every contract field except the hash itself. The order of hypotheses and claim identities is part of the request identity.

## Lineage rules

The supplied `NeutralReasoningTrace` must reference the exact supplied `ConstrainedReasoningResult`. Every supporting or contradicting claim hash must belong to the explicitly supplied immutable permitted-claim set. Duplicate hypothesis identifiers, duplicate claim hashes, and overlap between supporting and contradicting claims are rejected.

## Deferred semantics

L5.0 does not define hypothesis content. `HypothesisDefinition` is deferred to L5.1. Evidence-to-hypothesis relations, evaluation outcomes, and evaluation traces are deferred to later L5 milestones.

L5.0 introduces no probabilities, posterior updates, confidence scores, weights, rankings, preferred routes, trajectories, drift models, endpoint or location conclusions, search-area recommendations, or causal claims.
