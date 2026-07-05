# L6 Bayesian Evidence Fusion and Trajectory Ranking

## Purpose

L6 consumes deterministic trajectory hypotheses and residual evidence from L1-L5, then computes normalized posterior probabilities without changing the underlying physical models.

## Evidence model

Each `GaussianEvidence` term contains:

- an explicit evidence identifier;
- a residual supplied by an earlier deterministic layer;
- a caller-supplied positive standard deviation.

No historical calibration width or prior is embedded in the implementation.

## Likelihood model

For residual `r` and standard deviation `sigma`, the normalized Gaussian log-likelihood is:

```text
log L = -0.5 * (r^2 / sigma^2 + log(2 * pi * sigma^2))
```

`independent_log_likelihood` sums terms in log space. This function represents an explicit conditional-independence assumption selected by the caller. The software does not assert that real evidence sources are independent.

## Posterior model

Each trajectory supplies a non-negative prior and finite log-likelihood. The unnormalized log posterior is:

```text
log weight = log(prior) + log likelihood
```

Normalization uses log-sum-exp for numerical stability. A zero prior remains an impossible hypothesis with posterior probability zero.

## Ranking

Posterior records are sorted by descending probability. Equal probabilities are ordered by trajectory identifier, producing deterministic and replayable output.

## Failure discipline

L6 fails closed for:

- empty identifiers;
- duplicate evidence or trajectory identifiers;
- non-finite residuals, scales, priors, or log-likelihoods;
- non-positive Gaussian scales;
- negative priors;
- an empty hypothesis set;
- a hypothesis set with no positive prior.

## Scope boundaries

L6 does not perform MCMC, particle filtering, route search, learned inference, automatic prior selection, automatic uncertainty calibration, or modification of L1-L5 constraints. It provides a transparent baseline model for synthetic validation and later controlled extension.
