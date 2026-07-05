# L4 Candidate Admissibility and Constraint Evaluation

## Purpose

L4 evaluates candidate records against explicit residual tolerances. It is a deterministic gate over outputs from earlier layers:

- L1 provides reachability constraints.
- L2 provides BFO residuals.
- L3 provides BTO slant-range residuals.

The layer emits decision records. It does not rank candidates, infer likelihood, optimize a path, or select tolerances automatically.

## Data model

`ConstraintTolerance` stores the active tolerance thresholds. A tolerance set to `None` disables that constraint while preserving the corresponding residual in the decision record.

`CandidateResiduals` stores the residual values associated with one candidate.

`ConstraintDecision` records whether a constraint was enabled, whether it passed, the residual, and the tolerance used.

`CandidateAdmissibility` groups all constraint decisions and exposes an `admissible` property. A candidate is admissible only when every enabled constraint passes.

## Evaluation rule

For each enabled constraint:

```text
passed = abs(residual) <= tolerance
```

If a constraint is enabled but the residual is missing, the constraint fails. If a constraint is disabled, it is explicitly marked as not evaluated and does not affect final admissibility.

## Failure discipline

The layer fails closed when:

- candidate identifiers are empty;
- provided residuals are not finite;
- provided tolerances are not finite;
- provided tolerances are negative.

## Scope boundaries

L4 is not a probabilistic layer. It does not provide posterior scores, weights, optimization, smoothing, trajectory fitting, or search ranking. Those belong to later milestones after deterministic admissibility is stable.
