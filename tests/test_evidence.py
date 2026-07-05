"""Tests for L6 evidence records."""

import math

import pytest

from mh370_inverse_inference.inference.evidence import (
    GaussianEvidence,
    TrajectoryEvidence,
)


def test_gaussian_evidence_accepts_finite_residual_and_positive_sigma() -> None:
    evidence = GaussianEvidence(evidence_id="bfo", residual=-2.5, sigma=1.5)

    assert evidence.evidence_id == "bfo"
    assert evidence.residual == -2.5
    assert evidence.sigma == 1.5


def test_gaussian_evidence_requires_non_empty_identifier() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        GaussianEvidence(evidence_id="", residual=0.0, sigma=1.0)


def test_gaussian_evidence_rejects_non_finite_residual() -> None:
    with pytest.raises(ValueError, match="finite"):
        GaussianEvidence(evidence_id="bto", residual=math.inf, sigma=1.0)


def test_gaussian_evidence_requires_positive_finite_sigma() -> None:
    with pytest.raises(ValueError, match="positive"):
        GaussianEvidence(evidence_id="bto", residual=0.0, sigma=0.0)

    with pytest.raises(ValueError, match="finite"):
        GaussianEvidence(evidence_id="bto", residual=0.0, sigma=math.inf)


def test_trajectory_evidence_requires_at_least_one_term() -> None:
    with pytest.raises(ValueError, match="at least one"):
        TrajectoryEvidence(trajectory_id="trajectory-a", terms=())


def test_trajectory_evidence_requires_unique_evidence_ids() -> None:
    first = GaussianEvidence(evidence_id="bfo", residual=0.0, sigma=1.0)
    second = GaussianEvidence(evidence_id="bfo", residual=1.0, sigma=2.0)

    with pytest.raises(ValueError, match="unique"):
        TrajectoryEvidence(trajectory_id="trajectory-a", terms=(first, second))
