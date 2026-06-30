import pytest

from mh370_inverse_inference.satcom.validation import compare_loci
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


def test_validation_metrics_are_deterministic() -> None:
    generated = (
        GeodeticPoint(-30.0, 90.0),
        GeodeticPoint(-31.0, 91.0),
    )
    reference = (
        GeodeticPoint(-30.0, 90.0),
        GeodeticPoint(-31.0, 91.0),
    )

    first = compare_loci(
        generated,
        reference,
        benchmark_id="synthetic-identical",
        model_version="0.1.0",
    )
    second = compare_loci(
        generated,
        reference,
        benchmark_id="synthetic-identical",
        model_version="0.1.0",
    )

    assert first == second
    assert first.sample_count == 2
    assert first.mean_deviation_m == pytest.approx(0.0, abs=1e-9)
    assert first.maximum_deviation_m == pytest.approx(0.0, abs=1e-9)


def test_validation_reports_nonzero_deviation() -> None:
    generated = (GeodeticPoint(-30.0, 90.0),)
    reference = (GeodeticPoint(-30.0, 90.1),)

    metrics = compare_loci(
        generated,
        reference,
        benchmark_id="synthetic-offset",
        model_version="0.1.0",
    )

    assert metrics.sample_count == 1
    assert metrics.mean_deviation_m > 0.0
    assert metrics.maximum_deviation_m == pytest.approx(metrics.mean_deviation_m)


def test_empty_inputs_are_rejected() -> None:
    point = (GeodeticPoint(-30.0, 90.0),)
    with pytest.raises(ValueError):
        compare_loci((), point, benchmark_id="empty", model_version="0.1.0")
    with pytest.raises(ValueError):
        compare_loci(point, (), benchmark_id="empty", model_version="0.1.0")
