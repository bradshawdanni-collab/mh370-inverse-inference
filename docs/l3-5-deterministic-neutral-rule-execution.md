# L3.5 Deterministic Neutral Rule Execution

## Purpose

L3.5 is the first executable interpretation stage. It consumes one immutable
`InterpretationRequest`, applies one allowlisted neutral rule, emits one
`NeutralDerivedClaim`, and seals that claim into an `InterpretationResult`.

The layer performs structural rule execution only. It does not infer flight
paths, locations, causes, probabilities, rankings, or outcomes.

## Governing path

```text
InterpretationRequest
    -> NeutralRuleId
    -> NeutralDerivedClaim
    -> InterpretationResult
    -> NeutralRuleExecution
```

## Allowlisted rules

The executor exposes only fixed `NeutralRuleId` members:

- `SOURCE_PRESENT`
- `OBSERVATION_LINKED`
- `VALIDATION_PRESENT`
- `EVIDENCE_CONSUMED`

Each rule has a fixed claim type, fixed statement, fixed support-field mapping,
and fixed rule version. Callers cannot supply arbitrary rule bodies or claim
statements.

## Deterministic identities

Each execution records:

- the original request `input_hash`;
- the sealed result `output_hash`;
- an operation-signature hash covering the executor contract, operation, rule
  identity, rule version, and interpretation policy version;
- the exact rule ID and version;
- the complete deterministic `InterpretationResult`.

No clock, UUID, random value, environment value, filesystem state, network state,
or persistence layer contributes to any identity.

## Lineage rule

A generated claim may reference only the request's permitted content-addressed
lineage:

- `registry_evidence_id`
- `evidence_hash`
- `validation_hash`

The existing L3.4 result boundary independently validates that claim support
remains inside this lineage.

## Explicit exclusions

L3.5 does not provide:

- confidence or probability;
- likelihoods, weights, rankings, or Bayesian fusion;
- trajectory, drift, route, coordinate, endpoint, or location semantics;
- causal conclusions;
- registry lookup or authority reconstruction;
- raw-evidence retrieval;
- persistence, caching, synchronization, filesystem, network, or environment
  access;
- caller-defined executable rules.

## Completion condition

L3.5 is complete when an allowlisted neutral rule deterministically transforms
one `InterpretationRequest` into a content-addressed claim, result, and execution
record while introducing no substantive inference authority.
