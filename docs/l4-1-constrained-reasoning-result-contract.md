# L4.1 Constrained Reasoning Result Contract

## Purpose

L4.1 defines the immutable result envelope emitted from an L4.0 `ConstrainedReasoningRequest`.

```text
ConstrainedReasoningRequest
    -> ConstrainedReasoningResult
```

The contract records only structural reasoning disposition. It does not introduce substantive MH370 conclusions.

## Result surface

`ConstrainedReasoningResult` contains:

- the exact L4.0 `request_hash`;
- `reasoning_contract_version = "L4.1"`;
- the preserved reasoning policy version;
- a stable status;
- ordered reason codes;
- an empty immutable `reasoning_outputs` tuple;
- a deterministic `result_hash`.

The public dataclass constructor is disabled. Construction is permitted only through `build_constrained_reasoning_result(...)` using the exact L4.0 request type.

## Canonical identity

The result hash is computed with the repository `sha256_payload` helper over:

```text
request_hash
reasoning_contract_version
reasoning_policy_version
status
reason_codes
reasoning_outputs
```

`result_hash` is excluded from its own preimage. Reason-code order is identity-bearing.

## Statuses

- `ACCEPTED`
- `REJECTED`
- `INSUFFICIENT_BASIS`
- `CONSTRAINT_VIOLATION`

## Neutral output rule

For L4.1, `reasoning_outputs` is always empty. Structured rule-application records are deferred to L4.2.

## Boundary exclusions

L4.1 performs no evidence lookup, authority reconstruction, persistence, nondeterministic operation, scoring, ranking, update calculation, route analysis, drift analysis, endpoint analysis, location analysis, search-area prioritisation, or causal conclusion.

## Completion gate

The milestone is complete when the result envelope is deterministic, immutable, replayable, content-addressed, and passes Ruff, Black, mypy, pytest, and DX.2.
