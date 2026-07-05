# L6 Bayesian Evidence Fusion and Trajectory Ranking

## Purpose

L6 consumes deterministic outputs from L1-L5 and produces posterior probabilities and ranked trajectory hypotheses. It does not alter aircraft dynamics, satellite geometry, admissibility rules, or trajectory assembly.

## Pipeline

```text
Evidence schema
    -> Gaussian log-likelihoods
    -> posterior normalization
    -> deterministic ranking
```

## Explicit assumptions

### Discrete hypothesis set

Posterior normalization operates over the finite tuple of hypotheses supplied by the caller. The returned probabilities are normalized only across that supplied set. The implementation does not claim that the set is physically exhaustive unless the caller establishes that separately.

### Caller-supplied priors

Priors are inputs, not inferred constants. They must be finite and non-negative, with at least one positive prior. The implementation does not select priors automatically.

### Finite log-likelihoods

Each hypothesis must have a finite log-likelihood. Numerical normalization is performed with a log-sum-exp calculation to avoid underflow for strongly negative values.

### Zero-prior semantics

A zero prior denotes an impossible hypothesis under the supplied model. Its posterior remains exactly zero regardless of its likelihood.

### Conditional independence

The independent likelihood combiner sums log-likelihood terms. That operation is valid only when the caller deliberately adopts a conditional-independence model for the selected evidence terms. The software does not assert that BFO, BTO, timing, or trajectory evidence are inherently independent.

### Ranking semantics

Ranking sorts normalized posterior probabilities in descending order. Equal probabilities are ordered by trajectory identifier to make output deterministic and replayable. Ranking is not a physical validation step.

## Invariants

The L6 implementation preserves these invariants:

- evidence identifiers are non-empty;
- evidence identifiers within one trajectory bundle are unique;
- residuals and Gaussian scales are finite;
- Gaussian scales are positive;
- hypothesis identifiers are unique;
- priors are finite and non-negative;
- at least one prior is positive;
- log-likelihoods are finite;
- posterior probabilities are finite and within `[0, 1]`;
- posterior probabilities sum to one within floating-point tolerance;
- zero-prior hypotheses remain zero;
- adding the same constant to all log-likelihoods does not change normalized probabilities;
- ranking is deterministic for ties.

## Scope boundaries

L6 does not provide:

- automatic prior calibration;
- empirical uncertainty estimation;
- dependence correction between evidence sources;
- MCMC or particle filtering;
- route optimization;
- learned inference;
- claims about the real-world completeness of the hypothesis set.

## Verification strategy

L6 is verified through three bands:

1. unit tests for evidence, likelihoods, posterior normalization, and ranking;
2. contract tests for the data passed between L5 and L6;
3. one frozen synthetic end-to-end fixture after the L6 interfaces are stable.

The frozen fixture must be treated as a versioned artifact with provenance, explicit invariants, and a controlled update policy.
