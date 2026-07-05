"""Deterministic assembly and consistency checks for timestamped trajectories."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, isfinite, pi, sin, sqrt

from mh370_inverse_inference.aircraft.state import AircraftState

EARTH_RADIUS_M: float = 6_371_000.0


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    """One timestamped aircraft state in a candidate trajectory."""

    timestamp_s: float
    state: AircraftState
    candidate_admissible: bool | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.timestamp_s):
            raise ValueError("timestamp_s must be finite")


@dataclass(frozen=True, slots=True)
class TrajectoryLimits:
    """Explicit deterministic limits used for segment evaluation."""

    max_ground_speed_mps: float
    max_abs_climb_rate_mps: float
    max_abs_turn_rate_rad_s: float
    max_mass_increase_kg: float = 0.0
    require_candidate_admissibility: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("max_ground_speed_mps", self.max_ground_speed_mps),
            ("max_abs_climb_rate_mps", self.max_abs_climb_rate_mps),
            ("max_abs_turn_rate_rad_s", self.max_abs_turn_rate_rad_s),
            ("max_mass_increase_kg", self.max_mass_increase_kg),
        ):
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class SegmentMetrics:
    """Derived physical metrics for one consecutive state pair."""

    duration_s: float
    surface_distance_m: float
    implied_ground_speed_mps: float
    climb_rate_mps: float
    turn_rate_rad_s: float
    mass_change_kg: float


@dataclass(frozen=True, slots=True)
class SegmentDecision:
    """Deterministic consistency decision for one trajectory segment."""

    segment_index: int
    metrics: SegmentMetrics
    speed_ok: bool
    climb_ok: bool
    turn_ok: bool
    mass_ok: bool
    endpoints_admissible: bool | None

    @property
    def consistent(self) -> bool:
        """Return True when all enabled segment checks pass."""
        endpoint_ok = (
            True if self.endpoints_admissible is None else self.endpoints_admissible
        )
        return all(
            (
                self.speed_ok,
                self.climb_ok,
                self.turn_ok,
                self.mass_ok,
                endpoint_ok,
            )
        )


@dataclass(frozen=True, slots=True)
class TrajectoryEvaluation:
    """Complete deterministic evaluation of a candidate trajectory."""

    points: tuple[TrajectoryPoint, ...]
    segments: tuple[SegmentDecision, ...]

    @property
    def consistent(self) -> bool:
        """Return True when every segment is consistent."""
        return bool(self.segments) and all(
            segment.consistent for segment in self.segments
        )


def _great_circle_distance_m(first: AircraftState, second: AircraftState) -> float:
    latitude_delta = second.latitude - first.latitude
    longitude_delta = second.longitude - first.longitude
    haversine = sin(latitude_delta / 2.0) ** 2 + (
        cos(first.latitude)
        * cos(second.latitude)
        * sin(longitude_delta / 2.0) ** 2
    )
    central_angle = 2.0 * asin(min(1.0, sqrt(haversine)))
    return EARTH_RADIUS_M * central_angle


def _signed_heading_delta_rad(first_heading: float, second_heading: float) -> float:
    return (second_heading - first_heading + pi) % (2.0 * pi) - pi


def _segment_metrics(first: TrajectoryPoint, second: TrajectoryPoint) -> SegmentMetrics:
    duration_s = second.timestamp_s - first.timestamp_s
    if duration_s <= 0.0:
        raise ValueError("Trajectory timestamps must be strictly increasing")

    surface_distance_m = _great_circle_distance_m(first.state, second.state)
    return SegmentMetrics(
        duration_s=duration_s,
        surface_distance_m=surface_distance_m,
        implied_ground_speed_mps=surface_distance_m / duration_s,
        climb_rate_mps=(second.state.altitude - first.state.altitude) / duration_s,
        turn_rate_rad_s=(
            _signed_heading_delta_rad(first.state.heading, second.state.heading)
            / duration_s
        ),
        mass_change_kg=second.state.mass - first.state.mass,
    )


def evaluate_trajectory(
    points: tuple[TrajectoryPoint, ...], limits: TrajectoryLimits
) -> TrajectoryEvaluation:
    """Evaluate an ordered timestamped trajectory against explicit limits."""
    if len(points) < 2:
        raise ValueError("A trajectory requires at least two points")

    decisions: list[SegmentDecision] = []
    for index, (first, second) in enumerate(
        zip(points, points[1:], strict=False)
    ):
        metrics = _segment_metrics(first, second)
        endpoints_admissible: bool | None = None
        if limits.require_candidate_admissibility:
            endpoints_admissible = (
                first.candidate_admissible is True
                and second.candidate_admissible is True
            )
        decisions.append(
            SegmentDecision(
                segment_index=index,
                metrics=metrics,
                speed_ok=(
                    metrics.implied_ground_speed_mps <= limits.max_ground_speed_mps
                ),
                climb_ok=(
                    abs(metrics.climb_rate_mps) <= limits.max_abs_climb_rate_mps
                ),
                turn_ok=(
                    abs(metrics.turn_rate_rad_s)
                    <= limits.max_abs_turn_rate_rad_s
                ),
                mass_ok=metrics.mass_change_kg <= limits.max_mass_increase_kg,
                endpoints_admissible=endpoints_admissible,
            )
        )

    return TrajectoryEvaluation(points=points, segments=tuple(decisions))
