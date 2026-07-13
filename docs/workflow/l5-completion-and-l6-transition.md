# Repository workflow after L5 release

## Current workflow

```text
L1-L4
Evidence, interpretation, and reasoning foundations
        ↓
L5.0
HypothesisEvaluationRequest
        ↓
L5.1
HypothesisDefinition
        ↓
L5.2
EvidenceHypothesisRelationRecord
        ↓
L5.3
HypothesisEvaluationResult
        ↓
L5.4
HypothesisEvaluationTrace
        ↓
L5.5
Release freeze
        ↓
l5-v1.0.0 published
```

## Current status

- L5 implementation: complete
- CI and DX.2: passed
- release manifest: frozen
- replay fixture: hash locked
- GitHub release: published
- operational state: stable

## Next phase: L6 comparative hypothesis assessment

L6 introduces controlled structural comparison across frozen L5 evaluation results. It remains neutral and does not introduce probability, confidence, weighting, ranking, Bayesian updating, trajectory modelling, drift modelling, endpoint claims, location conclusions, or search-area recommendations.

```text
HypothesisEvaluationResult(s)
        +
HypothesisEvaluationTrace(s)
        ↓
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

## Planned L6 milestones

- L6.0 — `ComparativeAssessmentRequest`
- L6.1 — `ComparativeAssessmentRecord`
- L6.2 — `ComparativeAssessmentResult`
- L6.3 — `ComparativeAssessmentTrace`
- L6.4 — L6 release freeze

## First milestone

L6.0 defines the exact ordered set of frozen L5 results and traces permitted to enter comparison.

The contract must preserve exact result and trace identities, validate one-to-one lineage, reject duplicate inputs, require at least two distinct hypotheses, record an explicit comparison-policy version, and derive a deterministic canonical request hash through `sha256_payload`.

Tracking issue: #141.
