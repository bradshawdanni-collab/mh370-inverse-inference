"""Tests for the L9.1 Bayesian evidence fusion contract."""

import math
from dataclasses import FrozenInstanceError

import pytest

from mh370_inverse_inference.bayesian.contract import (
    EvidenceComponent,
    EvidenceRecord,
    EvidenceType,
    Hypothesis,
    fuse_evidence,
    log_sum_exp,
)


@pytest.fixture
def base_hypotheses() -> tuple[Hypothesis, ...]:
    return (
        Hypothesis(hypothesis_id="H-001", prior_weight=0.5),
        Hypothesis(hypothesis_id="H-002", prior_weight=0.3),
        Hypothesis(hypothesis_id="H-003", prior_weight=0.2),
    )


def test_exact_deterministic_bayesian_replay(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    component = EvidenceComponent(
        evidence_type=EvidenceType.BTO,
        source_id="SATCOM-BTO",
        records=(
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=math.log(0.8)),
            EvidenceRecord(hypothesis_id="H-002", log_likelihood=math.log(0.1)),
            EvidenceRecord(hypothesis_id="H-003", log_likelihood=math.log(0.1)),
        ),
    )

    first = fuse_evidence(base_hypotheses, (component,))
    second = fuse_evidence(base_hypotheses, (component,))
    probabilities = {entry.hypothesis_id: entry.posterior_probability for entry in first}

    assert first == second
    assert probabilities["H-001"] == pytest.approx(0.40 / 0.45)
    assert probabilities["H-002"] == pytest.approx(0.03 / 0.45)
    assert probabilities["H-003"] == pytest.approx(0.02 / 0.45)
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_impossible_hypothesis_normalizes_with_remaining_support(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    component = EvidenceComponent(
        evidence_type=EvidenceType.TRAJECTORY_CONSISTENCY,
        source_id="GEOGRAPHIC-BOUNDS",
        records=(
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=-math.inf),
            EvidenceRecord(hypothesis_id="H-002", log_likelihood=0.0),
            EvidenceRecord(hypothesis_id="H-003", log_likelihood=0.0),
        ),
    )

    results = fuse_evidence(base_hypotheses, (component,))
    probabilities = {entry.hypothesis_id: entry.posterior_probability for entry in results}

    assert probabilities["H-001"] == 0.0
    assert probabilities["H-002"] == pytest.approx(0.3 / 0.5)
    assert probabilities["H-003"] == pytest.approx(0.2 / 0.5)
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_all_impossible_hypotheses_fail_closed(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    component = EvidenceComponent(
        evidence_type=EvidenceType.NEGATIVE_SEARCH,
        source_id="TOTAL-EXCLUSION",
        records=tuple(
            EvidenceRecord(
                hypothesis_id=hypothesis.hypothesis_id,
                log_likelihood=-math.inf,
            )
            for hypothesis in base_hypotheses
        ),
    )

    with pytest.raises(ValueError, match="zero posterior support"):
        fuse_evidence(base_hypotheses, (component,))


def test_unknown_hypothesis_raises_provenance_error(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    malformed = EvidenceComponent(
        evidence_type=EvidenceType.DEBRIS_RECOVERY,
        source_id="ROGUE-DATASET",
        records=(EvidenceRecord(hypothesis_id="H-999", log_likelihood=-1.2),),
    )

    with pytest.raises(ValueError, match="unknown hypothesis"):
        fuse_evidence(base_hypotheses, (malformed,))


def test_duplicate_records_in_same_source_fail_closed(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    duplicate = EvidenceComponent(
        evidence_type=EvidenceType.BFO,
        source_id="MALFORMED-SENSOR-STREAM",
        records=(
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=-0.5),
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=-0.2),
        ),
    )

    with pytest.raises(ValueError, match="duplicate evidence record"):
        fuse_evidence(base_hypotheses, (duplicate,))


def test_evidence_order_does_not_change_posterior(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    bto = EvidenceComponent(
        evidence_type=EvidenceType.BTO,
        source_id="BTO-A",
        records=(
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=-0.1),
            EvidenceRecord(hypothesis_id="H-002", log_likelihood=-0.2),
            EvidenceRecord(hypothesis_id="H-003", log_likelihood=-0.3),
        ),
    )
    bfo = EvidenceComponent(
        evidence_type=EvidenceType.BFO,
        source_id="BFO-A",
        records=(
            EvidenceRecord(hypothesis_id="H-001", log_likelihood=-0.3),
            EvidenceRecord(hypothesis_id="H-002", log_likelihood=-0.2),
            EvidenceRecord(hypothesis_id="H-003", log_likelihood=-0.1),
        ),
    )

    first = fuse_evidence(base_hypotheses, (bto, bfo))
    second = fuse_evidence(base_hypotheses, (bfo, bto))

    first_probs = {entry.hypothesis_id: entry.posterior_probability for entry in first}
    second_probs = {entry.hypothesis_id: entry.posterior_probability for entry in second}
    assert first_probs == second_probs


def test_contributions_retain_type_and_provenance(
    base_hypotheses: tuple[Hypothesis, ...],
) -> None:
    component = EvidenceComponent(
        evidence_type=EvidenceType.NEGATIVE_SEARCH,
        source_id="SEARCH-NON-DETECTION-A",
        records=(EvidenceRecord(hypothesis_id="H-001", log_likelihood=-0.1),),
    )

    result = fuse_evidence((base_hypotheses[0],), (component,))[0]

    assert result.contributions[0].evidence_type is EvidenceType.NEGATIVE_SEARCH
    assert result.contributions[0].source_id == "SEARCH-NON-DETECTION-A"
    assert result.contributions[0].log_likelihood == -0.1


def test_log_sum_exp_is_stable_for_extreme_scores() -> None:
    value = log_sum_exp((-1000.0, -1001.0, -math.inf))

    assert math.isfinite(value)
    assert value == pytest.approx(-1000.0 + math.log1p(math.exp(-1.0)))


@pytest.mark.parametrize(
    ("hypotheses", "message"),
    [
        ((), "hypotheses cannot be empty"),
        ((Hypothesis("H-1", 1.0), Hypothesis("H-1", 0.5)), "unique"),
    ],
)
def test_invalid_hypothesis_sets_fail_closed(
    hypotheses: tuple[Hypothesis, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        fuse_evidence(hypotheses, ())


def test_invalid_records_fail_closed() -> None:
    with pytest.raises(ValueError, match="prior weight"):
        Hypothesis(hypothesis_id="H", prior_weight=-0.1)
    with pytest.raises(ValueError, match="NaN"):
        EvidenceRecord(hypothesis_id="H", log_likelihood=math.nan)
    with pytest.raises(ValueError, match="negative infinity"):
        EvidenceRecord(hypothesis_id="H", log_likelihood=math.inf)
    with pytest.raises(ValueError, match="records cannot be empty"):
        EvidenceComponent(
            evidence_type=EvidenceType.BTO,
            source_id="EMPTY",
            records=(),
        )


def test_output_records_are_immutable(base_hypotheses: tuple[Hypothesis, ...]) -> None:
    result = fuse_evidence((base_hypotheses[0],), ())[0]

    with pytest.raises(FrozenInstanceError):
        result.posterior_probability = 0.0
