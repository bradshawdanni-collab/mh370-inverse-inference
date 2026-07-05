"""Tests for L6 evidence records."""

import math

import pytest

from mh370_inverse_inference.inference.evidence import (
    GaussianEvidence,
    TrajectoryEvidence,
)


def test_gaussian_evidence_requires_positive_sigma() -> None:
    with pytest.raises(ValueError, match="positive"):
        GaussianEvidence(evidence_id="bfo", residual=0.0, sigma=0.0)


def test_gaussian_evidence_rejects_non_finite_residual() -> None:
    with pytest.raises(ValueError, match="finite"):
        GaussianEvidence(evidence_id="bto", residual=math.inf, sigma=1.0)


def test_trajectory_evidence_requires_unique_ids() -> None:
    term = GaussianEvidence(evidence_id="bfo", residual=0.0, sigma=1.0)
    with pytest.raises(ValueError, match="unique"):
        TrajectoryEvidence(trajectory_id="t1", terms=(term, term))
