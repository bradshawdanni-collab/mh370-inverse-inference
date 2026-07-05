"""Tests for L6 Gaussian likelihood functions."""

import pytest

from mh370_inverse_inference.inference.evidence import (
    GaussianEvidence,
    TrajectoryEvidence,
)
from mh370_inverse_inference.inference.likelihood import (
    gaussian_log_likelihood,
    independent_log_likelihood,
)


def test_zero_residual_has_higher_likelihood_than_nonzero_residual() -> None:
    zero = GaussianEvidence(evidence_id="zero", residual=0.0, sigma=2.0)
    offset = GaussianEvidence(evidence_id="offset", residual=3.0, sigma=2.0)

    assert gaussian_log_likelihood(zero) > gaussian_log_likelihood(offset)


def test_independent_log_likelihood_sums_terms() -> None:
    first = GaussianEvidence(evidence_id="bto", residual=1.0, sigma=2.0)
    second = GaussianEvidence(evidence_id="bfo", residual=-0.5, sigma=1.5)
    evidence = TrajectoryEvidence(trajectory_id="t1", terms=(first, second))

    assert independent_log_likelihood(evidence) == pytest.approx(
        gaussian_log_likelihood(first) + gaussian_log_likelihood(second)
    )
