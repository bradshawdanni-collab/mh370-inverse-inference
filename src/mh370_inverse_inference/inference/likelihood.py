"""Likelihood functions for explicit evidence records."""

from __future__ import annotations

from math import isfinite, log, pi

from mh370_inverse_inference.inference.evidence import (
    GaussianEvidence,
    TrajectoryEvidence,
)


def gaussian_log_likelihood(evidence: GaussianEvidence) -> float:
    """Return the normalized Gaussian log-likelihood for one residual."""
    variance = evidence.sigma * evidence.sigma
    result = -0.5 * (
        evidence.residual * evidence.residual / variance + log(2.0 * pi * variance)
    )
    if not isfinite(result):
        raise ValueError("log-likelihood must be finite")
    return result


def independent_log_likelihood(evidence: TrajectoryEvidence) -> float:
    """Sum evidence terms in log space under an explicit independence model."""
    result = sum(gaussian_log_likelihood(term) for term in evidence.terms)
    if not isfinite(result):
        raise ValueError("combined log-likelihood must be finite")
    return result
