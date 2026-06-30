"""Deterministic validation metrics for generated and reference BTO loci."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean

from mh370_inverse_inference.satcom.geometry import geodesic_distance_m
from mh370_inverse_inference.satcom.wgs84 import GeodeticPoint


@dataclass(frozen=True, slots=True)
class ValidationMetrics:
    """Summary statistics for generated-to-reference locus deviation."""

    benchmark_id: str
    model_version: str
    sample_count: int
    mean_deviation_m: float
    maximum_deviation_m: float


def nearest_reference_distance_m(
    point: GeodeticPoint,
    reference_points: tuple[GeodeticPoint, ...],
) -> float:
    """Return the nearest WGS84 geodesic distance to a reference point."""
    if not reference_points:
        raise ValueError("reference_points must not be empty")
    return min(geodesic_distance_m(point, reference) for reference in reference_points)


def compare_loci(
    generated_points: tuple[GeodeticPoint, ...],
    reference_points: tuple[GeodeticPoint, ...],
    *,
    benchmark_id: str,
    model_version: str,
) -> ValidationMetrics:
    """Compare generated points with a reference locus using nearest distances."""
    if not generated_points:
        raise ValueError("generated_points must not be empty")
    if not reference_points:
        raise ValueError("reference_points must not be empty")

    deviations = tuple(
        nearest_reference_distance_m(point, reference_points)
        for point in generated_points
    )
    return ValidationMetrics(
        benchmark_id=benchmark_id,
        model_version=model_version,
        sample_count=len(deviations),
        mean_deviation_m=fmean(deviations),
        maximum_deviation_m=max(deviations),
    )
