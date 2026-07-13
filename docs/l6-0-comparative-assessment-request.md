# L6.0 Comparative Assessment Request

## Purpose

`ComparativeAssessmentRequest` is the deterministic entry contract for the L6 comparative-assessment layer.

It binds an exact ordered set of frozen L5 hypothesis-evaluation results and their matching traces into one neutral comparison input.

```text
HypothesisEvaluationResult(s)
        +
HypothesisEvaluationTrace(s)
        ↓
ComparativeAssessmentRequest
```

## Contract surface

The request preserves:

- `ordered_evaluation_result_hashes`;
- `ordered_evaluation_trace_hashes`;
- `comparison_policy_version`;
- `comparative_contract_version`;
- canonical `request_hash`.

The object is frozen, slotted, content addressed, and unavailable through its public constructor.

## Admission rules

A valid request requires:

- at least two distinct L5 evaluation results;
- at least two distinct hypothesis identities across the supplied results;
- exactly one trace for each result;
- matching result-to-trace order;
- trace lineage back to its paired result;
- no duplicate result hashes;
- no duplicate trace hashes;
- a non-blank comparison-policy version.

Changing result order, trace order, or policy version changes the canonical request hash.

## Neutrality boundary

L6.0 authorizes structural admission into comparison only. It does not calculate or assert:

- probability or confidence;
- evidence weights;
- hypothesis ranking;
- Bayesian updates;
- trajectory or drift models;
- endpoints, coordinates, or locations;
- search-area conclusions;
- causal truth.

Those meanings are outside the L6.0 contract.

## Determinism

The canonical payload is serialized through the repository hashing kernel and sealed with `sha256_payload`.

No clock, UUID, randomness, filesystem, network, persistence, database, or registry authority participates in request identity.

## Planned L6 sequence

```text
L6.0  ComparativeAssessmentRequest
L6.1  ComparativeAssessmentRecord
L6.2  ComparativeAssessmentResult
L6.3  ComparativeAssessmentTrace
L6.4  L6 release freeze
```

## Verification gate

The contract is not merge-ready until all repository gates pass:

- Ruff;
- Black;
- mypy;
- pytest;
- DX.2 compliance.
